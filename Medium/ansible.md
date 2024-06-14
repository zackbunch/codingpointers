# Writing Custom Ansible Modules

Over the past three years, I have worked as a Site Reliability Engineer (SRE). My primary task has been to automate myself out of a job, which mainly focused on creating wrappers around APIs for the applications we use. However, our team is a mixed bag of engineers - some are developers, while others are more focused on infrastructure. This diversity means that writing Ansible playbooks and coding can sometimes be challenging.

To address this, we have decided to eventually split our team to bridge the hiring gap, focusing on hiring individuals who don't necessarily need to know how to code but are expected to be proficient with Ansible. As a part of this transition, I have started converting our Python packages into custom Ansible modules. This approach simplifies the process for non-developers, making it easier for them to leverage the power of Ansible without needing deep programming knowledge.

In this tutorial, we will create a custom pip package to interact with SonarQube, as well as a custom Ansible module that non-developers can use. Here's an overview of the steps we'll follow to achieve this:

1. Spin up a SonarQube instance using Docker
2. Write a pip package to interact with the SonarQube API
3. Create a custom Ansible module using the pip package
4. Write Ansible playbooks to use the custom module to automate the setup of SonarQube

## Spinning up the SonarQube Edition

For this tutorial, we will be using SonarQube community edition using Docker. I have provided a Dockerfile located on my GitHub that we will use to quickly get the Docker Instance spun up. Feel free to star the repo for later use.

Please [click here](https://github.com/zackbunch/codingpointers) to get the Dockerfile.

---

## Setting Up SonarQube with Docker Compose

In this tutorial, we will set up SonarQube and PostgreSQL using Docker Compose. SonarQube is an open-source platform used to continuously inspect the code quality and security of your codebases. By using Docker Compose, we can easily define and run multi-container Docker applications.

**Step 1: Create the Docker Compose File**

First, create a directory for your project and navigate into it. Then, create a file named `docker-compose.yml` with the following content:

```yaml
version: '3'
services:
  sonarqube:
    image: sonarqube:latest
    ports:
      - 9000:9000
    environment:
      - SONARQUBE_JDBC_USERNAME=sonar
      - SONARQUBE_JDBC_PASSWORD=sonar
      - SONARQUBE_JDBC_URL=jdbc:postgresql://db:5432/sonar
    depends_on:
      - db
    container_name: sonarqube

  db:
    image: postgres:latest
    environment:
      - POSTGRES_USER=sonar
      - POSTGRES_PASSWORD=sonar
      - POSTGRES_DB=sonar
    ports:
      - 5432:5432
    container_name: sonarqube_db
```
**Step 2: Start the services**
Run the follwing command to start the SonarQube and PostgreSQL service:

```sh
docker-compose up -d
```
The -d flag runs the containers in detached mode, meaning they will run in the background.

**Step 3: Access SonarQube**

Open your web browser and go to http://localhost:9000. You should see the SonarQube interface. The default login credentials are usually:

	•	Username: admin
	•	Password: admin
After logging in for the first time, you will be prompted to change the default password. Follow the instructions to set a new password. This step is crucial for securing your SonarQube instance.

---

## Generating a SonarQube Token

After setting up SonarQube and changing the default password, the next step is to generate a token. This token will be used to authenticate API requests to SonarQube, which is essential for automating tasks and integrating SonarQube with other tools.

**Step 1: Log in to SonarQube**

1. Open your web browser and go to `http://localhost:9000`.
2. Log in with your new credentials.

**Step 2: Generate a Token**

1. Click on your profile picture in the top-right corner of the SonarQube interface and select **My Account**.
2. Navigate to the **Security** tab.
3. In the **Generate Tokens** section, provide a name for your token (e.g., `ansible-module`).
4. Click on the **Generate** button.
5. Copy the generated token and store it in a secure location. You will not be able to see the token again once you navigate away from the page.

## Writing a pip Package to interact with the SonarQube API

With SonarQube set up and a token generated, the next step is to create a pip package that interacts with the SonarQube API. This package will simplify the process of making API requests and will be used in the custom Ansible module.

**Step 1: Create a New Python Package**
```sh
mkdir sonarqube
```
**Step 2: Create the necessary files for your package**:
•	setup.py
•	README.md
•	sonarqube_api/__init__.py
•	sonarqube_api/sonarqube.py