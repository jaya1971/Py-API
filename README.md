---

Deploy a Python API to an Azure App service with Azure container registry and Azure DevOps

---
![image](https://github.com/jaya1971/Py-API/assets/43556775/45ee8ce2-779f-481b-998b-060ff67fe465)
---
Objective

This post is to show how to publish a docker container image to an Azure Container registry, then deploy that image to Azure App Service. The web API will require a connection to an On-Prem database in a SQL server instance using the App Services' Hybrid connection feature. This uses a very simple python API creation calling stored procedures on a SQL server that returns results in a JSON format. The repository can be found here.

Repository: https://github.com/jaya1971/Py-API

Requirements
1. Basic understanding of Azure App Services, Azure DevOps and Docker.
2. An account with Azure cloud and Azure DevOps.

Overview
1. Create an Azure container registry.
2. Configure the Dockerfile with the necessary updates and installs, along with other references to data that will be brought over from the pipeline, through the Dockerfile and into the API.
3. Create a Docker Registry service connection.
4. Create a library group in your Azure DevOps project to host your secret variables and SQL information.
5. Create a pipeline to build and push the image to the Azure Container Registry.
6. Create an App Service in Azure with predefined settings.
7. Pipeline to deploy the CR image to the App Service.
8. Configure pipeline environment variables and pass them from the pipeline to the Python API.
9. Configure the App Service Hybrid connection to interact with an On-Prem SQL server and database.

Automation Order
I would like to point out that I have two pipelines for automating this process. One for deploying an azure container registry and App Service through terraform. The other for the python API. Because the creation and deployment of an Azure container app service must occur in a certain order. I have parameterized my pipelines with Booleans to run certain parts of the automation so I can deploy resources in a specific order.
Here is the order of deployment:
1. Create an Azure Container Registry to hold your docker image (Manual or through Terraform)(I used a terraform module pipeline).
2. Build and push an image to the Azure Container Registry (I ran this from this current repository in a pipeline by setting the " Update docker image repo" to True).
3. Create a Linux container azure app service (Manual or through Terraform)(I used a terraform module pipeline). When creating a Linux container azure app service, you must reference the image in the container registry. This is why it is done after pushing the image to the container registry.
4. Deploy image to the Linux container app service. (I ran this from this current repository in a pipeline by setting "Deploy img to app service" to True).

Walkthrough
1. I created a main YAML pipeline to call template YAML based on conditions so it would be able to deploy it to different environments. You'll notice in my repository, that I'm deploying it to dev or prod. This YAML file is what the pipeline uses when triggered. This YAML file is parameterized. The parameters will select a template at runtime.
  a. In the main "azure-pipelines.yml" file lines 32–45 contain the variables and library group used to pass variables to the called YAML files.
    i. Line 33,34 app: Application name.
    ii. Line 35,36 repo: The repository created when you pushed the image to the container registry
    iii. Line 39,40 docker_img_path: is comprised of "<loginServer>/<repository>:<ImageTag>
    iv. Lines 47–57 contain the references to the called YAML files in the 'azurepipelines' folder.
    v. Lines 59–71 contain the stages and conditions to determine which YAML file to use.
  
2. Template YAML files.
  a. The called pipelines are broken into two jobs: "Build and Push the Image" and "Deploy Image to App Service".
    i. The first job "BuildAndPushImage" contains three tasks: "printAllVariables@1", and two "Docker@2".
      1. printAllVariables@1: lists all pipeline variables. This is great for reviewing directory and artifact locations along with variable information. Secret variable values are not displayed.
      2. Docker@2: One is to Build the docker image and the other is to push the docker image to the container registry. Variables used are a hybrid of variables declared in the entry YAML template, ADO project library and project service connection.
      3. The "arguments" on line 27 contain the variables from the library group that will be used in the python application.
    ii. The second job "DeployImageToAppService" contains two tasks: "AzureWebContainer@1" and "AzureAppServiceSettings@1".
      1. AzureWebContainer@1: Will deploy the image from the container registry to the app service.
      2. AzureAppServiceSettings@1: Contains additional configuration settings.
  
3. This takes care of the basic setup of having your API's image in the acr and deployed to your App Service. Since we're working with an On-Prem database we'll need to configure a connection that will allow us to access the On-Prem SQL. If you navigate to your App Service's Log stream (Under Monitoring), you'll notice an error message that reads something like: "pyodbc.OperationalError: ('HYT00', u'[HYT00]……..". This usually indicates that you do not have a valid connection to your data source, in our case, our On-Prem SQL server. We'll also have to configure a way to pass the connection string information so our API will properly connect to our data source. The objective is to keep sensitive information hidden. We can do this by creating environment pipeline variables. There are various ways you can do this in Azure DevOps:
  a. Environment variables
    i. Pipeline variables - make sure you mark sensitive values as secret. Pipeline variables are kept in your pipeline and separate from your repository.
    ii. Library Group variables - These are ADO's library groups where you will be able to configure environment variables to be used by your pipelines. The library groups can be secured to all pipelines in your project or to specific ones. You can either place your variables directly in this group or sync it with a keyvault located in your Azure subscription. (Link your keyvault to your ADO Library Group)
  b. Once you've chosen how you will store your environment variables, you will want to pass these values to your API in your py app. I've intentionally named the variables/parameters slightly different to make it easier to distinguish which direction they are being passed. The process is to:
    i. Create the reference in your pipeline.
      1) This is reference in lines 32–45 in the main YAML pipeline file.
    ii. Pass those variables in the template YAML files.
      1) Arguments on line 27 will pass these variables to the Dockerfile.
    iii. Pass those values to your Dockerfile as parameters.
      1) Dockerfile: Lines 5–12 contain the passed variables from the YAML file as "ARG"
      2) They are converted into environment variables using the ENV tag.
  
      iv. In the py app file, you can reference the environment variables passed by the Dockerfile as "os.getenv('<ENV_VARIABLENAME>')
4. Now since we're connecting to an On-Prem SQL server, you'll still receive an error message that references a bad connection to your data source and that's because in this case we are trying to connect to an On-Prem data source. If your data source was an Azure SQL server, you would be able to successfully run your app service API. Let's configure a hybrid connection to our On-Prem SQL Server. (Great article with step by step - Hybrid Connection)
  a. In your Azure app service, navigate to Settings >> Networking >> Hybrid connections >> Add hybrid connection >> Create new hybrid connection. Create your hybrid connection. Your endpoint should be the SQL fqdn that can be found by an On-Prem node where you will install the hybrid connection agent. Copy the "Gateway Connection String", you'll need it when you install the agent On-Prem.
  b. Download the connection manager to install on an On-Prem node. When creating the connection, select manual and paste the "Gateway Connection String" you copied in the previous step. Restart the "Azure Hybrid Connection Manager Service". Then your hybrid connection should reflect as:
  ![image](https://github.com/jaya1971/Py-API/assets/43556775/e99d241d-ee12-461a-96bc-a297779609b2)

Challenges and things learned
There were a few challenges and issues that popped up during this development. One of them being how to pass environmental variables to python, which is different depending on the method being used. The others are listed below.
1. SQL Server instances. We have MS SQL Server configured with instances. When I first configured the hybrid connection, it read successful and connected but I was still receiving the pyodbc connection error message. This was because instances use different ports rather than the default 1433. This can be found in SQL Server Configuration Manager >> SQL Server Network Configuration >> Protocols >> TCP/IP >> IP Addresses tab, under IPAll, you will find the TCP Dynamic Port being used. You'll want to reference the instance in your ADO Pipeline as "server.domain.com,PORTNUMBER"
2. After everything was up and running, it seemed that the connection to the sql server was still busy with another query and would return an error message that read like: "Error # HY000 [Microsoft][ODBC SQL Server Driver]Connection is busy with results for another hstmt)". I found that setting the MARS (Multiple Active Result Sets) reference in your pyodbc connection string would resolve this issue. This is referenced in Line 38 of the main.py file: "MARS_Connection=YES"
  
Hope you found this useful!
