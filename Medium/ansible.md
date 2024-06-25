# Creating Custom Ansible Modules

Over the past three years, I have worked as a Site Reliability Engineer (SRE). My primary task has been to automate myself out of a job, which mainly focused on creating wrappers around APIs for the applications we use. However, our team is a mixed bag of engineers - some are developers, while others are more focused on infrastructure. This diversity means that writing Ansible playbooks and coding can sometimes be challenging.

To address this, I have started converting our Python packages into custom Ansible modules. This approach simplifies the process for non-developers, making it easier for them to leverage the power of Ansible without needing deep programming knowledge.

In this tutorial, we will create a custom pip package to interact with SonarQube, as well as a custom Ansible module that non-developers can use. Here's an overview of the steps we'll follow to achieve this:

1. Spin up a SonarQube instance using Docker
2. Write a pip package to interact with the SonarQube API
3. Create a custom Ansible module using the pip package
4. Write Ansible playbooks to use the custom module to automate the setup of SonarQube

## Spin up a SonarQube instance using Docker

For this tutorial, we will be using SonarQube community edition using Docker. I have provided a Dockerfile located on my GitHub that we will use to quickly get the Docker Instance spun up. Feel free to star the repo for later use.

Please [click here](https://github.com/zackbunch/codingpointers/blob/ansible/Medium/docker-compose.yml) to get the Dockerfile.

### Setting Up SonarQube with Docker Compose

In this section, we will set up SonarQube and PostgreSQL using Docker Compose. SonarQube is an open-source platform used to continuously inspect the code quality and security of your codebases. By using Docker Compose, we can easily define and run multi-container Docker applications.

#### Step 1: Create the Docker Compose File

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

#### Step 2: Start the Services

```sh
docker-compose up -d
```

The -d flag runs the containers in detached mode, meaning they will run in the background.

#### Step 3: Access SonarQube

Open your web browser and go to <http://localhost:9000>. You should see the SonarQube interface. The default login credentials are usually:

- Username: admin
- Password: admin

After logging in for the first time, you will be prompted to change the default password. Follow the instructions to set a new password. This step is crucial for securing your SonarQube instance.

## Write a pip package to interact with the SonarQube API

With SonarQube set up and a token generated, the next step is to create a pip package that interacts with the SonarQube API. This package will simplify the process of making API requests and will be used in the custom Ansible module.

#### Step 1: Create a New Python Package

```sh
mkdir sonarqube
```

#### Step 2: Create the Necessary Files for Your Package

- setup.py
- README.md
- sonarqube/init.py
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

#### Step 3: Set up the Package

Edit the setup.py to include the following information:

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

#### Step 4: Create Core Functionality

Create a core.py class to include the following information:

```python
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class Core:
    """
    Core class to interact with the SonarQube API.

    Attributes:
        url (str): Base URL of the SonarQube server.
        session (requests.Session): A Requests session for making HTTP calls.
    """

    def __init__(self, url: str, token: str):
        """
        Initialize the Core instance.

        Args:
            url (str): Base URL of the SonarQube server.
            token (str): Token for API access.
        """
        self.url = url
        self.session = requests.Session()
        self.session.auth = (token, "")

    def endpoint_url(self, endpoint: str) -> str:
        """
        Construct the full URL for a given API endpoint.

        Args:
            endpoint (str): The API endpoint to append to the base URL.

        Returns:
            str: The full URL for the API call.
        """
        return f"{self.url}{endpoint}"

    def call(
        self,
        method: callable,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP call using the provided method, endpoint, and data.

        Args:
            method (callable): The HTTP method to use (e.g., session.get, session.post).
            endpoint (str): The API endpoint to call.
            expected_status_codes (list of int, optional): List of expected status codes. Defaults to None.
            params (dict, optional): Optional query parameters. Defaults to None.
            data (dict, optional): Optional data to pass in the request (as form data). Defaults to None.

        Returns:
            Any: The JSON response from the API.

        Raises:
            Exception: If the HTTP request fails or the response status is an error.
        """
        url = self.endpoint_url(endpoint)
        logger.debug(f"Making request to {url} with params {params} and data {data}")
        try:
            if method == self.session.get:
                response = method(url, params=params)
            else:
                response = method(url, data=data)
            if (
                expected_status_codes
                and response.status_code not in expected_status_codes
            ):
                raise requests.HTTPError(
                    f"Unexpected status code: {response.status_code}", response=response
                )
            response.raise_for_status()
            try:
                return response.json() if response.text else {}
            except ValueError:
                return response.text
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            logger.error(
                f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}"
            )
            raise Exception(
                f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}"
            )

    def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a POST request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.post, endpoint, expected_status_codes=[200, 201], data=data
        )

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send a GET request.

        Args:
            endpoint (str): The API endpoint to call.
            params (dict, optional): The query parameters to send in the request. Defaults to None.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.get, endpoint, expected_status_codes=[200], params=params
        )

    def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a PUT request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.put, endpoint, expected_status_codes=[200], data=data
        )

    def delete(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a DELETE request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(self.session.delete, endpoint, data=data)

```

#### Step 5: Create Group Functionality

Creating the Group class is a critical part of our solution as it encapsulates all the operations related to user groups in SonarQube. This class will include methods for creating, updating, deleting, and retrieving user groups. An important aspect of these methods is ensuring idempotence, meaning that repeated applications of these operations will yield the same result. This is crucial for the reliability and predictability of our Ansible module.

Class Definition and Initialization

The Group class will hold an instance of the Core class to interact with the SonarQube API. By holding an instance of the Core class, the Group class can leverage its functionality without being tightly coupled to its implementation. This separation of concerns enhances modularity and makes the codebase easier to maintain and extend.

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

Get Group ID by Name

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
            raise InsufficientPrivilegesException(
                "Insufficient privileges to perform this action. Please check the token permissions."
            )
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

By adding the key changed to the response and setting it to True, we indicate that the operation resulted in a change. In Ansible, this is useful for tracking whether the state of the system has been altered by a task, allowing Ansible to report on changes.

#### Step 6: Create a Custom Ansible Module Using the Pip Package

Install Ansible

To get started working on the Ansible module, we need to install Ansible. It is available as a pip package and can be installed simply like this:

```sh
pip3 install ansible
```

Create a New Folder for the Ansible Module

Now that we have Ansible installed, we can begin by creating our module that utilizes our newly created SonarQube pip package. Let’s create a new folder in the root of our project and name it ansible_modules. Inside this folder, we will create a new file and name it `group.py`. This new file will serve as the Ansible Module.

```sh
mkdir ansible_modules
touch ansible_modules/group.py
```

Write the Ansible Module

Edit the group.py file to include the following code, which defines the Ansible module using the SonarQube pip package.

We will begin by adding our neccessary imports to get started.

```python
#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from sonarqube.core import Core
from sonarqube.group import Group
from sonarqube.exceptions import GroupAlreadyExistsException, GroupNotFoundException, UnexpectedResponseException
```

Take note of `AnsibleModule`, this is what provides the basic functionality needed to handle module arguments and return results. The rest of the imports are from our newly created pip package.

Module Initialization

Next, we need to define the module arguments and initialize the Ansible module. This involves specifying the parameters that the module will accept.

```python
#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from sonarqube.core import Core
from sonarqube.group import Group
from sonarqube.exceptions import GroupAlreadyExistsException, GroupNotFoundException, UnexpectedResponseException

def run_module():
    module_args = dict(
        url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=False),
        description=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True, choices=['present', 'absent'])
        
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
```

The meat and potatos of this code are inside `module_args`. This is where all possible arguments the module will accept need to be defined. These arguments are essential for specifying the details of the task you want the module to perform. Let’s break down each argument defined in `module_args`:

### Module Arguments

| Argument      | Type   | Required | Default | Description |
|---------------|--------|----------|---------|-------------|
| `url`         | `str`  | Yes      | -       | The URL of the SonarQube server. This is mandatory for the module to run as it tells the module where to send the API requests. |
| `token`       | `str`  | Yes      | -       | The authentication token for accessing the SonarQube API. This is necessary for authenticating requests. It is marked as `no_log=True` to ensure that the token is not logged, protecting sensitive information. |
| `name`        | `str`  | No       | -       | The name of the group. While optional, it is generally required for creating or deleting a group. |
| `description` | `str`  | No       | `None`  | An optional description for the group. You can provide additional details about the group, but it is not necessary for the module to function. |
| `state`       | `str`  | Yes      | -       | Specifies the desired state of the group. The state can be either `present` (to ensure the group exists) or `absent` (to ensure the group is deleted). Possible choices are `present` and `absent`. |