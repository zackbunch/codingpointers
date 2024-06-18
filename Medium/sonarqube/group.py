from typing import Any, Optional

from sonarqube.core import Core
from sonarqube.exceptions import (
    InsufficientPrivilegesException,
    GroupNotFoundException,
    GroupAlreadyExistsException,
    UnexpectedResponseException
)


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

    def create_group(self, name: str) -> Any:
        """
        Create a new user group in SonarQube if it does not already exist.

        Args:
            name (str): The name of the group to create.

        Returns:
            Any: The response from the SonarQube API.
        
        Raises:
            GroupAlreadyExistsException: If the group already exists.
        """
        try:
            group_id = self.get_group_id(name)
            if group_id is not None:
                raise GroupAlreadyExistsException(f"Group '{name}' already exists.")
        except GroupNotFoundException:
            pass  # If group is not found, it means we can proceed to create it

        endpoint = "/api/user_groups/create"
        data = {"name": name}
        try:
            response = self.core.post(endpoint=endpoint, **data)
        except Exception as e:
            if "already exists" in str(e):
                raise GroupAlreadyExistsException(f"Group '{name}' already exists.")
            else:
                raise e
        response["changed"] = True
        return response

    def update_group(self, id: str, name: str) -> Any:
        """
        Update an existing user group in SonarQube if the name is different.

        Args:
            id (str): The ID of the group to update.
            name (str): The new name of the group.

        Returns:
            Any: The response from the SonarQube API.
        
        Raises:
            GroupNotFoundException: If the group does not exist.
        """
        current_id = self.get_group_id(name)
        if current_id == id:
            return {"msg": "Group already has the desired name", "changed": False}
        
        endpoint = "/api/user_groups/update"
        data = {"id": id, "name": name}
        response = self.core.post(endpoint=endpoint, **data)
        response["changed"] = True
        return response

    def delete_group(self, id: str) -> Any:
        """
        Delete a user group in SonarQube if it exists.

        Args:
            id (str): The ID of the group to delete.

        Returns:
            Any: The response from the SonarQube API.
        
        Raises:
            GroupNotFoundException: If the group does not exist.
        """
        endpoint = "/api/user_groups/delete"
        data = {"id": id}
        response = self.core.post(endpoint=endpoint, **data)
        response["changed"] = True
        return response

    def get_group_id(self, name: str) -> Optional[str]:
        """
        Get the ID of a user group by name.

        Args:
            name (str): The name of the group to search for.

        Returns:
            Optional[str]: The ID of the group if found, None otherwise.
        
        Raises:
            InsufficientPrivilegesException: If the user does not have privileges to perform the action.
            GroupNotFoundException: If the group is not found.
            UnexpectedResponseException: If the API response is unexpected.
        """
        endpoint = "/api/user_groups/search"
        try:
            response = self.core.get(endpoint=endpoint, q=name)
            groups = response.get("groups", [])
            for group in groups:
                if group.get("name") == name:
                    return group.get("id")
            raise GroupNotFoundException(f"Group with name '{name}' not found.")
        except Exception as e:
            if "403" in str(e):
                raise InsufficientPrivilegesException("Insufficient privileges to perform this action. Please check the token permissions.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
        return None