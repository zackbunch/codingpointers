from os import makedirs, path
from typing import Any, Dict, List, Optional

import requests
import urllib3

class Core:
    """
    A class to interact with the Sonar API.

    Attributes:
        url (str): Base URL of the Sonar server.
        token (str): Token for API access.
        session (requests.Session): A Requests session for making HTTP calls.
    """

    def __init__(self, url: str, token: str, verify_ssl: bool = False):
        """
        Initialize the SonarCore instance.

        Args:
            url (str): Base URL of the Sonar server.
            token (str): Token for API access.
            verify_ssl (bool): Whether to verify SSL certificates.
        """
        self.url = url
        self.session = requests.Session()
        self.session.verify = verify_ssl
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if token:
            self.session.auth = (token, '')
        else:
            raise ValueError("Authentication credentials are not provided. Set the token parameter.")

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
        **data: Dict[str, Any],
    ) -> Any:
        """
        Make an HTTP call using the provided method, endpoint, and data.

        Args:
            method (callable): The HTTP method to use (e.g., session.get, session.post).
            endpoint (str): The API endpoint to call.
            expected_status_codes (list[int], optional): List of expected status codes. Defaults to None.
            **data (dict): Optional data to pass in the request (as JSON or query params).

        Returns:
            Any: The JSON response from the API.

        Raises:
            Exception: If the HTTP request fails or the response status is an error.
        """
        url = self.endpoint_url(endpoint)
        try:
            if method in [
                self.session.get,
                self.session.post,
                self.session.put,
                self.session.delete,
            ]:
                response = method(url, **data)

            if expected_status_codes and response.status_code not in expected_status_codes:
                raise Exception(
                    f"Unexpected status code: {response.status_code}, URL: {url}, Data: {data}"
                )
            response.raise_for_status()
            try:
                return response.json() if response.text else {}
            except ValueError:
                return response.text
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            raise Exception(
                f"HTTP error occurred: {str(e)}, URL: {url}, Data: {data}, Error Data: {error_data}"
            )
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}, URL: {url}, Data: {data}")

    def post(
        self,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        **data: Dict[str, Any],
    ) -> Any:
        """Send POST requests."""
        return self.call(self.session.post, endpoint, expected_status_codes, **data)

    def get(
        self,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        **data: Dict[str, Any],
    ) -> Any:
        """Send GET requests."""
        return self.call(self.session.get, endpoint, expected_status_codes, **data)

    def put(
        self,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        **data: Dict[str, Any],
    ) -> Any:
        """Send PUT requests."""
        return self.call(self.session.put, endpoint, expected_status_codes, **data)

    def delete(
        self,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        **data: Dict[str, Any],
    ) -> Any:
        """Send DELETE requests."""
        return self.call(self.session.delete, endpoint, expected_status_codes, **data)