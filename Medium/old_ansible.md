# Writing Custom Ansible Modules

Over the past three years, I have worked as a Site Reliability Engineer (SRE). My primary task has been to automate myself out of a job, which mainly focused on creating wrappers around APIs for the applications we use. However, our team is a mixed bag of engineers - some are developers, while others are more focused on infrastructure. This diversity means that writing Ansible playbooks and coding can sometimes be challenging.

To address this, I have started converting our Python packages into custom Ansible modules. This approach simplifies the process for non-developers, making it easier for them to leverage the power of Ansible without needing deep programming knowledge.

In this tutorial, we will create a custom pip package to interact with SonarQube, as well as a custom Ansible module that non-developers can use. Here's an overview of the steps we'll follow to achieve this:

1. Spin up a SonarQube instance using Docker
2. Write a pip package to interact with the SonarQube API
3. Create a custom Ansible module using the pip package
4. Write Ansible playbooks to use the custom module to automate the setup of SonarQube

## Spinning up the SonarQube Edition

For this tutorial, we will be using SonarQube community edition using Docker. I have provided a Dockerfile located on my GitHub that we will use to quickly get the Docker Instance spun up. Feel free to star the repo for later use.

Please [click here](https://github.com/zackbunch/codingpointers/blob/ansible/Medium/docker-compose.yml) to get the Dockerfile.

---

## Setting Up SonarQube with Docker Compose

In this tutorial, we will set up SonarQube and PostgreSQL using Docker Compose. SonarQube is an open-source platform used to continuously inspect the code quality and security of your codebases. By using Docker Compose, we can easily define and run multi-container Docker applications.

### Step 1: Create the Docker Compose File

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

### Step 2: Start the services

Run the follwing command to start the SonarQube and PostgreSQL service:

```sh
docker-compose up -d
```

The -d flag runs the containers in detached mode, meaning they will run in the background.

### Step 3: Access SonarQube

Open your web browser and go to <http://localhost:9000>. You should see the SonarQube interface. The default login credentials are usually:

 • Username: admin
 • Password: admin
After logging in for the first time, you will be prompted to change the default password. Follow the instructions to set a new password. This step is crucial for securing your SonarQube instance.

---

## Generating a SonarQube Token

After setting up SonarQube and changing the default password, the next step is to generate a token. This token will be used to authenticate API requests to SonarQube, which is essential for automating tasks and integrating SonarQube with other tools.

### Step 1: Log in to SonarQube

1. Open your web browser and go to `http://localhost:9000`.
2. Log in with your new credentials.

### Step 2: Generate a Token

1. Click on your profile picture in the top-right corner of the SonarQube interface and select **My Account**.
2. Navigate to the **Security** tab.
3. In the **Generate Tokens** section, provide a name for your token (e.g., `ansible-module`).
4. Click on the **Generate** button.
5. Copy the generated token and store it in a secure location. You will not be able to see the token again once you navigate away from the page.

## Writing a pip Package to interact with the SonarQube API

With SonarQube set up and a token generated, the next step is to create a pip package that interacts with the SonarQube API. This package will simplify the process of making API requests and will be used in the custom Ansible module.

### Step 1: Create a New Python Package

```sh
mkdir sonarqube
```

### Step 2: Create the necessary files for your package

- setup.py
- README.md
- sonarqube/**init**.py
- sonarqube/core.py

The structure of your package should look like this:

```sh
sonarqube/
├── README.md
├── setup.py
└── sonarqube/
    ├── __init__.py
    └── core.py
```

### Step 3: Set up the Package

1. Edit the setup.py to include the following information:

```python
from setuptools import setup, find_packages

setup(
    name='sonarqube',
    version='0.0.1',
    author='Zack Bunch',
    author_email='zackbunch96@gmail.com',
    url='https://www.youtube.com/@codingpointers',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    description='A Python package to interact with the SonarQube API',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
```

### Step 2: Create core functionality

1. Create a core.py class to include the following information:

```python
import requests
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Core:
    def __init__(self, url: str, token: str):
        self.url = url
        self.session = requests.Session()
        self.session.auth = (token, '')

    def endpoint_url(self, endpoint: str) -> str:
        return f"{self.url}{endpoint}"

    def call(self, method: callable, endpoint: str, expected_status_codes: Optional[List[int]] = None, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
        url = self.endpoint_url(endpoint)
        logger.debug(f"Making request to {url} with params {params} and data {data}")
        try:
            if method == self.session.get:
                response = method(url, params=params)
            else:
                response = method(url, data=data)
            if expected_status_codes and response.status_code not in expected_status_codes:
                raise requests.HTTPError(f"Unexpected status code: {response.status_code}", response=response)
            response.raise_for_status()
            try:
                return response.json() if response.text else {}
            except ValueError:
                return response.text
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            logger.error(f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}")
            raise Exception(f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}")

    def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        return self.call(self.session.post, endpoint, expected_status_codes=[200, 201], data=data)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.call(self.session.get, endpoint, expected_status_codes=[200], params=params)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        return self.call(self.session.put, endpoint, expected_status_codes=[200], data=data)

    def delete(self, endpoint: str, data: Dict[str, Any]) -> Any:
        return self.call(self.session.delete, endpoint, expected_status_codes=[204], data=data)
```

### Step 3: Create group functionality

Creating the Group class is a critical part of our solution as it encapsulates all the operations related to user groups in SonarQube. This class will include methods for creating, updating, deleting, and retrieving user groups. An important aspect of these methods is ensuring **idempotence**, meaning that repeated applications of these operations will yield the same result. This is crucial for the reliability and predictability of our Ansible module.

Let’s break down the Group class into bite-sized pieces that are easy to understand.

1. Create a new module called `group.py` under the sonarqube package

We will begin by importing the necessary modules and set up logging. This helps in debugging and tracking the operations performed by the class.

```python
from typing import Any, Optional, List, Dict
import logging

from sonarqube.core import Core
from sonarqube.exceptions import (
    InsufficientPrivilegesException,
    GroupNotFoundException,
    GroupAlreadyExistsException,
    UnexpectedResponseException
)

logger = logging.getLogger(__name__)
```

2. Class Definition and Initialization

The Group class will hold an instance of the Core class to interact with the SonarQube API.
By holding an instance of the Core class, the Group class can leverage its functionality without being tightly coupled to its implementation. This separation of concerns enhances modularity and makes the codebase easier to maintain and extend.

```python
class Group:
    """
    A class to interact with the SonarQube user groups API.

    Attributes:
        core (Core): An instance of the Core class to interact with the SonarQube API.
    """

    def __init__(self, core: Core):
        """
        Initialize the Group instance.

        Args:
            core (Core): An instance of the Core class to interact with the SonarQube API.
        """
        self.core = core
```

We will start by writing our first function to truly interact with SonarQube in a useful way. The function will create a group in SonarQube. To write this function in such a way that it follows the principle of idempotence, we must first check if the group already exists before attempting to create it. While we could combine all the logic into one function, we will create a helper function first that gets the group ID of a given group name. If the name does not exist, we can proceed with creating the new group.

```python

def get_group_id(self, name: str) -> Optional[str]:
        """
        Get the ID of a user group by name.

        Args:
            name (str): The name of the group to search for.

        Returns:
            Optional[str]: The ID of the group if found, None otherwise.

        Raises:
            InsufficientPrivilegesException: If the user does not have privileges to perform the action.
            UnexpectedResponseException: If the API response is unexpected.
        """
        endpoint = "/api/user_groups/search"
        try:
            response = self.core.get(endpoint=endpoint, params={"q": name})
            groups = response.get("groups", [])
            for group in groups:
                if group.get("name") == name:
                    return group.get("id")
            return None  # Group not found, return None
        except Exception as e:
            if "403" in str(e):
                raise InsufficientPrivilegesException("Insufficient privileges to perform this action. Please check the token permissions.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
```

Create a New Group

Next, we will write the function to create a new group. This function will use the get_group_id helper function to check if the group already exists before attempting to create it. This ensures idempotence by preventing duplicate groups from being created.

```python
def create_group(self, name: str, description: Optional[str] = None) -> Any:
    """
    Create a new user group in SonarQube if it does not already exist.

    Args:
        name (str): The name of the group to create.
        description (str, optional): The description for the new group.

    Returns:
        Any: The response from the SonarQube API.

    Raises:
        GroupAlreadyExistsException: If the group already exists.
        UnexpectedResponseException: If the API response is unexpected.
    """
    group_id = self.get_group_id(name)
    if group_id is not None:
        raise GroupAlreadyExistsException(f"Group '{name}' already exists.")

    endpoint = "/api/user_groups/create"
    data = {"name": name}
    if description:
        data["description"] = description
    logger.debug(f"Creating group with data: {data}")
    try:
        response = self.core.post(endpoint=endpoint, data=data)
    except Exception as e:
        if "already exists" in str(e):
            raise GroupAlreadyExistsException(f"Group '{name}' already exists.")
        else:
            raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
    response["changed"] = True
    return response
```

You may have noticed that we add a key of changed to the response and explicitly set it to True. We do this in anticipation of using it in the future Ansible Module we will create. By adding the key to the response, it indicates that the operation resulted in a change. In Ansible, this is useful for tracking whether the state of the system has been altered by a task, allowing Ansible to report on changes.


### Step 6: Creating an Ansible Module
To get started working on the Ansible module, we will need to install Ansible. It is available as a pip package and can be installed simply like this:

```sh
pip3 install ansible
```

Now that we have Ansible installed, we can begin by creating our module that utilizes our newly created SonarQube pip package. Let’s start by creating a new folder in the root of our project and name it ansible_modules. Inside this folder, we will create a new file and name it `group.py`.

```sh
mkdir ansible_modules
touch ansible_modules/group.py
```

Inside `group.py`, we will write our Ansible module to manage SonarQube groups. Ansible modules are Python scripts that follow a specific structure and use the `AnsibleModule` helper to handle input and output.

### Writing the Ansible Module

```python
#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from sonarqube.core import Core
from sonarqube.group import Group
from sonarqube.exceptions import GroupAlreadyExistsException, GroupNotFoundException, UnexpectedResponseException

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = module.params['name']
    description = module.params['description']
    state = module.params['state']
    url = module.params['url']
    token = module.params['token']

    core = Core(url=url, token=token)
    group = Group(core=core)

    try:
        if state == 'present':
            group.create_group(name=name, description=description)
            result['changed'] = True
            result['message'] = f"Group '{name}' created successfully."
        elif state == 'absent':
            group.delete_group(name=name)
            result['changed'] = True
            result['message'] = f"Group '{name}' deleted successfully."
    except GroupAlreadyExistsException:
        result['message'] = f"Group '{name}' already exists."
    except GroupNotFoundException:
        result['message'] = f"Group '{name}' does not exist."
    except UnexpectedResponseException as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```