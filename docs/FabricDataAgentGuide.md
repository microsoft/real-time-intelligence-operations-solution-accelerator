# Fabric Data Agent Guide

After you have deployed your solution, you can add Azure Data Agent to get data analysis features from Fabric built-in AI capabilities. You can follow [Microsoft's Fabric Data Agent Guide](https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent) to create and set up your Fabric Data Agent, and use the materials provided here to set up your agent quickly. For example, you can 

- Create a Fabric Data Agent with a name, for example, `RTI_Data_Agent`,
- Add the EventHouse created in the Fabric workspace as your data source,
- Use the Agent configuration files provided below to set up your Fabric Data Agent. 

## 📁 Agent Configuration Files

This folder contains essential configuration files for setting up your Fabric Data Agent to deliver optimal intelligence based on your data.

### Core Setup Files

**[Agent Instructions - Master Prompt](./fabric_data_agent/agent_instructions.md)**  
Contains the primary instructions and behavior guidelines for your Fabric Data Agent. This file establishes the agent's role, scope, and response patterns.

**[Data Source Instructions](./fabric_data_agent/data_source_instructions.md)**  
Provides detailed information about your data structure, table relationships, and query patterns. This helps the agent understand your data and deliver more accurate, efficient responses.

**[Example Queries](./fabric_data_agent/example_queries.md)**  
Training pairs that map business questions to proven KQL queries. These examples help your data agent learn optimal response patterns for common manufacturing scenarios.

### Testing Files

**[Test Sample Questions](./fabric_data_agent/sample_test_questions.md)**  
A collection of sample questions you can use to test your agent's performance and evaluate response quality. Ideal for sharing with your testing team to jumpstart validation efforts.

## 💡 Customization Tips

- Replace sample data references with your organization's actual data structure
- Add domain-specific terminology and business context to the master instructions
- Include your most common business questions in the training examples
- Update query patterns to match your specific analytics needs





