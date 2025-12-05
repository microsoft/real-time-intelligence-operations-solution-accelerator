# Fabric Data Agent Guide

After you have deployed your solution, you can add Azure Data Agent to get data analysis features from Fabric built-in AI capabilities. You can follow [Microsoft's Fabric Data Agent Guide](https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent) to create and set up your Fabric Data Agent, and use the materials provided here to set up your agent quickly. For example, you can create a mew item, search for 'data agent', you will be presented the clickable resource to create a Fabric Data Agent. 

- Create a Fabric Data Agent with a name, for example, `RTI_Data_Agent`,
- Add the KQL Database created in the Fabric workspace as your data source,
- Use the Agent configuration files provided below to set up your Fabric Data Agent. 

## 📁 Agent Configuration Files

This folder contains essential configuration files for setting up your Fabric Data Agent to deliver optimal intelligence based on your data.

### Core Setup Files

**[Agent Instructions - Master Prompt](./fabric_data_agent/agent_instructions.md)**  
Contains the primary instructions and behavior guidelines for your Fabric Data Agent. This file establishes the agent's role, scope, and response patterns.

**[Data Source Description](./fabric_data_agent/data_source_descriptions.md)**  
Provides description about the data source. 

**[Data Source Instructions](./fabric_data_agent/data_source_instructions.md)**  
Provides detailed information about your data structure, table relationships, and query patterns. This helps the agent understand your data and deliver more accurate, efficient responses.

**[Example Queries](./fabric_data_agent/example_queries.md)**  
Training pairs that map business questions to proven KQL queries. These examples help your data agent learn optimal response patterns for common manufacturing scenarios.

### Testing the Data Agent

Once the Data Agent is set up with the above agent configuration files, you will be able to chat with the agent right away. You can also publish your data agent for others to use. Below is the user interface you can expect ([link to more sample test questions](./fabric_data_agent/sample_test_questions.md)): 

![Fabric Data Agent UI](../docs/images/deployment/fabric_data_agent_ui.png)

## 💡 Customization Tips

- Replace sample data references with your organization's actual data structure
- Add domain-specific terminology and business context to the master instructions
- Include your most common business questions in the training examples
- Update query patterns to match your specific analytics needs





