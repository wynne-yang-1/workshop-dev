# Lab 3: Validate the Agent Flow

## Introduction

The agent is built — now it's time to see it in action. In this lab, you'll use the Agent Flow Playground to test the Entertainment Release & Performance Analyst agent with a series of real-world questions that span box office analysis, streaming health, marketing ROI, and cross-title comparisons. Each test is designed to exercise a different combination of the agent's tools (RAG, SQL, or both) and demonstrate how the agent reasons across structured and unstructured data to serve marketing, finance, and content strategy teams.

Pay close attention to how the agent decides which tools to call, how it resolves title names to IDs (even with typos), and how it synthesizes results into clear, actionable business language.

**Estimated Time:** 15 Minutes

### Objectives

In this lab you will:

1. Open the Agent Flow Playground and create a test session
2. Test the agent with a multi-title box office question — observing how it resolves title names and handles typos
3. Test market-specific follow-ups to see how the agent maintains conversational context
4. Test marketing ROI and channel breakdown queries spanning multiple campaigns
5. Test streaming performance with a cross-title comparison request
6. Test the agent's ability to produce structured tabular output on demand

### Prerequisites

This lab assumes you have:

* Completed Lab 2 (Agent Flow Setup)
* The agent flow attached to an active AI Compute
* All tools (1 RAG + 7 SQL) configured and connected to the agent node

## Task 1: Open the Playground

The Playground is a built-in testing environment where you can create sessions and have conversations with your agent flow before deploying it to production.

1. From the agent flow canvas, click the **Test** button in the toolbar. This reveals the Playground panel.

2. In the chat window, click the **+** button to start a new test session with the agent you created.

3. The session is now active. You can type natural language questions in the chat input and the agent will reason, call tools, and respond — just as it would in production.

    > **Tip**: As you test, watch the tool call indicators. The Playground shows which tools the agent invokes, what parameters it passes, and what data comes back. This transparency is invaluable for understanding and debugging the agent's reasoning.

## Task 2: Test Box Office Performance — Multi-Title Query

In this step, you'll ask the agent about box office performance for two movies. Notice how the agent handles a misspelled title name ("skyline hiest" instead of "skyline heist") — it should use the `get_title_id` tool to resolve the correct title.

1. In the Playground chat, enter the following prompt:

    ```
    Can you tell me how well the movies neon knights and skyline hiest did at the box office?
    ```

2. Observe the agent's response. It should:
    - Recognize both title names (despite the typo in "skyline hiest")
    - Call the `get_title_id` tool to resolve the title names to their IDs
    - Call the `get_box_office_weekend` tool for each title
    - Return box office gross, screen counts, and ranking data
    - Present the results in structured, business-friendly language

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent identifies both titles, resolves the typo, retrieves box office data, and presents a comparative summary.

## Task 3: Test Market-Specific Follow-Up

Now test the agent's ability to handle a follow-up question that narrows the scope to a specific market. The agent should maintain context from the previous question.

1. In the same session, enter the following prompt:

    ```
    Can you look at the canadian market?
    ```

2. Observe the agent's response. It should:
    - Understand from context that you're still asking about Neon Knights and Skyline Heist
    - Resolve "canadian market" to the appropriate market code (CA)
    - Call the `get_box_office_weekend` tool with the Canadian market code for both titles
    - Present the Canadian box office results

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent maintains conversational context, resolves the market name to a code, and returns Canada-specific box office data for both titles.

## Task 4: Test Marketing ROI — Campaign Spend and Channel Breakdown

This step tests the marketing analysis capabilities. The agent needs to identify the campaigns associated with the two movies, retrieve spend and ROI data, and break it down by marketing channel.

1. In the same session, enter the following prompt:

    ```
    How about the campaign spend for these movies? What's the breakdown per channel?
    ```

2. Observe the agent's response. It should:
    - Use the `get_campaign_code` tool to find campaign IDs associated with both titles
    - Call the `get_campaign_summary` tool for each campaign to get total spend, revenue, and ROI
    - Call the `get_campaign_channel_breakdown` tool for each campaign to show spend by channel (e.g., social, programmatic, TV, search)
    - Present a clear comparison of marketing performance across both titles

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent chains multiple tool calls — first resolving campaigns, then retrieving summaries, then channel breakdowns — and synthesizes the results into an actionable marketing analysis.

## Task 5: Test Cross-Title Channel Comparison

This step tests the agent's ability to reason across the data it already retrieved and answer a comparative analytical question.

1. In the same session, enter the following prompt:

    ```
    Are the top channels the same for both movies?
    ```

2. Observe the agent's response. It should:
    - Compare the channel breakdown data from the previous response (or re-query if needed)
    - Identify which channels performed best for each movie
    - Highlight similarities and differences
    - Offer interpretation grounded in the data

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent provides a clear comparative analysis of channel performance, noting which channels are shared top performers and which differ between titles.

## Task 6: Test Streaming Performance — Multi-Title Comparison

This step shifts to streaming data and tests the agent's ability to handle a completely different data domain within the same session.

1. In the same session, enter the following prompt:

    ```
    Can you give me a report on streaming for cosmic kitchen and maple street?
    ```

2. Observe the agent's response. It should:
    - Resolve the title names (which may be partial or informal) using `get_title_id`
    - Call `get_streaming_trend` for each title
    - Return weekly streaming metrics: starts, hours streamed, and completion rates
    - Present the data as a comparative report

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent switches data domains from box office to streaming seamlessly, retrieves multi-week trend data for both titles, and presents it in a report format.

## Task 7: Test Structured Output — Custom Table Format

This final test evaluates the agent's ability to produce formatted tabular output when explicitly requested.

1. In the same session, enter the following prompt:

    ```
    Can you return a table for me? The columns are the two shows and the rows are the weeks. Just focus on the US market.
    ```

2. Observe the agent's response. It should:
    - Understand the request for a specific table layout (shows as columns, weeks as rows)
    - Filter to the US market only
    - Re-query if necessary, or restructure the data from the previous response
    - Return a clean, well-formatted table comparing both shows week by week

    > **Sample response placeholder**:
    >
    > *[Insert screenshot of agent response here]*
    >
    > Expected behavior: The agent restructures the data into the requested pivot-style table format, with weeks as rows and the two show titles as column headers, filtered to US market only.

## Task 8: Reflect on the Agent's Behavior

Before moving on, take a moment to consider what just happened across the test session.

1. **Tool selection**: The agent automatically determined which tools to call based on each question — RAG for policy questions, SQL for metrics, reference lookups for resolving names and codes.

2. **Context retention**: The agent maintained conversational context across turns — understanding that "these movies" referred to Neon Knights and Skyline Heist, and that the streaming question introduced new titles.

3. **Error tolerance**: The agent handled a misspelled title name ("skyline hiest") by using the reference lookup tool rather than failing.

4. **Multi-tool chaining**: For the marketing questions, the agent chained multiple tool calls — first resolving campaigns, then fetching summaries, then fetching channel breakdowns — before synthesizing a response.

5. **Output flexibility**: The agent adapted its response format from narrative summaries to structured tables based on the user's explicit request.

    > **Discussion prompt**: "If this agent were available to your team today, what would be the first question you'd ask about your current release? What additional data sources or tools would make it more useful?"

## Lab 3 Recap

In this lab, you validated the Entertainment Release & Performance Analyst agent across a comprehensive set of real-world scenarios:

- Multi-title box office queries with typo handling
- Market-specific follow-ups with conversational context retention
- Marketing ROI analysis with multi-tool chaining (campaign lookup → summary → channel breakdown)
- Cross-title comparative analysis
- Streaming performance reports across a different data domain
- Custom structured output formatting on demand

The agent successfully combined RAG (internal policy documents) and SQL (structured database queries) to serve the kinds of questions that marketing, finance, and content strategy teams ask every day. In the next lab, you'll deploy the agent to a production endpoint.

## Learn More

* [Oracle AI Data Platform — Sample Agent Flows on GitHub](https://github.com/oracle-samples/oracle-aidp-samples/tree/main/ai/agent-flows)
* [Oracle AI Data Platform — Documentation](https://docs.oracle.com/en/cloud/paas/ai-data-platform/)

## Acknowledgements

* **Author(s)** - Jean-Rene Gauthier [AIDP]
* **Contributors** - Eli Schilling - Cloud Architect, Gareth Nathan - SDE, GenAI
* **Last Updated By/Date** - Published March 2026
