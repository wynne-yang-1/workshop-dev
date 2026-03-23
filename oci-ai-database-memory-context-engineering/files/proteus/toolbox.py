"""
Proteus Toolbox
===============
Semantic tool registry — tools are discovered by meaning, not by name.
Supports LLM-powered docstring augmentation and synthetic query generation
for improved retrieval.
"""

import inspect
import uuid
import json
from typing import Callable, Optional, Union

from pydantic import BaseModel

from proteus import config


def get_embedding(text: str, embedding_model) -> list[float]:
    """Get the embedding for a text using the given embedding model."""
    return embedding_model.embed_query(text)


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    description: str
    signature: str
    parameters: dict
    return_type: str


class Toolbox:
    """
    Toolbox for registering, storing, and retrieving tools with LLM-powered augmentation.

    Tools are stored with embeddings for semantic retrieval, allowing Proteus to
    find relevant research tools based on natural language queries.
    """

    def __init__(self, memory_manager, llm_client, embedding_model, model: str = None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        self.model = model or config.OPENAI_MODEL
        self._tools: dict[str, Callable] = {}
        self._tools_by_name: dict[str, Callable] = {}

    def _augment_docstring(self, docstring: str) -> str:
        """Use LLM to improve and expand a tool's docstring for better retrieval."""
        if not docstring.strip():
            return "No description provided."

        prompt = f"""You are a technical writer. Improve the following function docstring to be more clear,
            comprehensive, and useful. Include:
            1. A clear concise summary
            2. Detailed description of what the function does
            3. When to use this function
            4. Any important notes or caveats

            Original docstring:
            {docstring}

            Return ONLY the improved docstring, no other text.
        """

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def _generate_queries(self, docstring: str, num_queries: int = 5) -> list[str]:
        """Generate synthetic example queries that would lead to using this tool."""
        prompt = f"""Based on the following tool description, generate {num_queries} diverse example queries
            that a user might ask when they need this tool. Make them natural and varied.

            Tool description:
            {docstring}

            Return ONLY a JSON array of strings, like: ["query1", "query2", ...]
        """

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=300,
        )

        try:
            queries = json.loads(response.choices[0].message.content.strip())
            return queries if isinstance(queries, list) else []
        except json.JSONDecodeError:
            return [response.choices[0].message.content.strip()]

    def _get_tool_metadata(self, func: Callable) -> ToolMetadata:
        """Extract metadata from a function for storage and retrieval."""
        sig = inspect.signature(func)

        parameters = {}
        for name, param in sig.parameters.items():
            param_info = {"name": name}
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            if param.default != inspect.Parameter.empty:
                param_info["default"] = str(param.default)
            parameters[name] = param_info

        return_type = "Any"
        if sig.return_annotation != inspect.Signature.empty:
            return_type = str(sig.return_annotation)

        return ToolMetadata(
            name=func.__name__,
            description=func.__doc__ or "No description",
            signature=str(sig),
            parameters=parameters,
            return_type=return_type,
        )

    def register_tool(
        self, func: Optional[Callable] = None, augment: bool = False
    ) -> Union[str, Callable]:
        """
        Register a function as a tool in the toolbox.

        Can be used as a decorator or called directly:

            @toolbox.register_tool
            def my_tool(): ...

            @toolbox.register_tool(augment=True)
            def my_enhanced_tool(): ...
        """

        def decorator(f: Callable) -> str:
            docstring = f.__doc__ or ""
            signature = str(inspect.signature(f))
            object_id = uuid.uuid4()
            object_id_str = str(object_id)

            if augment:
                augmented_docstring = self._augment_docstring(docstring)
                queries = self._generate_queries(augmented_docstring)

                embedding_text = (
                    f"{f.__name__} {augmented_docstring} {signature} {' '.join(queries)}"
                )
                embedding = get_embedding(embedding_text, self.embedding_model)

                tool_data = self._get_tool_metadata(f)
                tool_data.description = augmented_docstring

                tool_dict = {
                    "_id": object_id_str,
                    "embedding": embedding,
                    "queries": queries,
                    "augmented": True,
                    **tool_data.model_dump(),
                }
            else:
                embedding = get_embedding(
                    f"{f.__name__} {docstring} {signature}", self.embedding_model
                )
                tool_data = self._get_tool_metadata(f)

                tool_dict = {
                    "_id": object_id_str,
                    "embedding": embedding,
                    "augmented": False,
                    **tool_data.model_dump(),
                }

            self.memory_manager.write_toolbox(
                f"{f.__name__} {docstring} {signature}", tool_dict
            )

            self._tools[object_id_str] = f
            self._tools_by_name[f.__name__] = f
            return object_id_str

        if func is None:
            return decorator
        return decorator(func)
