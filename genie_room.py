import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import backoff
import pandas as pd
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from token_minter import TokenMinter, TokenMinterConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class GenieEnvConfig(BaseModel):
    """
    Configuration for Genie API access loaded from environment variables.
    """

    space_id: str = Field(..., description="Genie space identifier")
    host: str = Field(..., description="Databricks workspace hostname (without scheme)")

    @classmethod
    def from_env(cls) -> "GenieEnvConfig":
        return cls(
            space_id=os.environ.get("SPACE_ID"),
            host=os.environ.get("DATABRICKS_HOST"),
        )


class GenieAttachmentText(BaseModel):
    content: Optional[str] = None


class GenieAttachmentQuery(BaseModel):
    query: Optional[str] = None


class GenieAttachment(BaseModel):
    attachment_id: Optional[str] = None
    text: Optional[GenieAttachmentText] = None
    query: Optional[GenieAttachmentQuery] = None

    class Config:
        extra = "allow"


class GenieMessage(BaseModel):
    """
    Pydantic representation of a Genie message payload.
    """

    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[GenieAttachment]] = None

    class Config:
        extra = "allow"


class GenieStartConversationResponse(BaseModel):
    """
    Minimal fields returned when starting a conversation.
    """

    conversation_id: str
    message_id: str

    class Config:
        extra = "allow"


class GenieQueryResult(BaseModel):
    """
    Wrapper around the Genie query result payload to make access safer.
    """

    statement_response: Dict[str, Any] = Field(default_factory=dict)

    @property
    def data_array(self) -> List[Any]:
        return self.statement_response.get("result", {}).get("data_array", []) or []

    @property
    def schema(self) -> Dict[str, Any]:
        return self.statement_response.get("manifest", {}).get("schema", {}) or {}


# Initialize configuration using Pydantic
env_config = GenieEnvConfig.from_env()
SPACE_ID = env_config.space_id
DATABRICKS_HOST = env_config.host

token_minter_config = TokenMinterConfig.from_env()
token_minter = TokenMinter(config=token_minter_config)


class GenieClient:
    def __init__(self, host: str, space_id: str):
        self.host = host
        self.space_id = space_id
        self.update_headers()
        
        self.base_url = f"https://{host}/api/2.0/genie/spaces/{space_id}"
    
    def update_headers(self) -> None:
        """Update headers with fresh token from token_minter"""
        self.headers = {
            "Authorization": f"Bearer {token_minter.get_token()}",
            "Content-Type": "application/json"
        }
    
    @backoff.on_exception(
        backoff.expo,
        Exception,  
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def start_conversation(self, question: str) -> GenieStartConversationResponse:
        """Start a new conversation with the given question"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/start-conversation"
        payload = {"content": question}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return GenieStartConversationResponse.parse_obj(response.json())
    
    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def send_message(self, conversation_id: str, message: str) -> GenieMessage:
        """Send a follow-up message to an existing conversation"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages"
        payload = {"content": message}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return GenieMessage.parse_obj(response.json())

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def get_message(self, conversation_id: str, message_id: str) -> GenieMessage:
        """Get the details of a specific message"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return GenieMessage.parse_obj(response.json())

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def get_query_result(self, conversation_id: str, message_id: str, attachment_id: str) -> Dict[str, Any]:
        """Get the query result using the attachment_id endpoint"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        parsed = GenieQueryResult.parse_obj(response.json())

        # Maintain the original return structure while leveraging Pydantic parsing
        return {
            "data_array": parsed.data_array,
            "schema": parsed.schema,
        }

    @backoff.on_exception(
        backoff.expo,
        Exception,  # Retry on any exception
        max_tries=5,
        factor=2,
        jitter=backoff.full_jitter,
        on_backoff=lambda details: logger.warning(
            f"API request failed. Retrying in {details['wait']:.2f} seconds (attempt {details['tries']})"
        )
    )
    def execute_query(self, conversation_id: str, message_id: str, attachment_id: str) -> Dict[str, Any]:
        """Execute a query using the attachment_id endpoint"""
        self.update_headers()  # Refresh token before API call
        url = f"{self.base_url}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/execute-query"
        
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    

    def wait_for_message_completion(self, conversation_id: str, message_id: str, timeout: int = 300, poll_interval: int = 2) -> GenieMessage:
        """
        Wait for a message to reach a terminal state (COMPLETED, ERROR, etc.).
        
        Args:
            conversation_id: The ID of the conversation
            message_id: The ID of the message
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            The completed message
        """
        
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < timeout:
            message = self.get_message(conversation_id, message_id)
            status = message.status

            if status in ["COMPLETED", "ERROR", "FAILED"]:
                return message
                
            time.sleep(poll_interval)
            attempt += 1
            
        raise TimeoutError(f"Message processing timed out after {timeout} seconds")

def start_new_conversation(question: str) -> Tuple[str, Union[str, pd.DataFrame], Optional[str]]:
    """
    Start a new conversation with Genie.
    
    Args:
        question: The initial question
        
    Returns:
        Tuple containing:
        - conversation_id: The new conversation ID
        - response: Either text or DataFrame response
        - query_text: SQL query text if applicable, otherwise None
    """
    
    client = GenieClient(
        host=DATABRICKS_HOST,
        space_id=SPACE_ID,
    )
    
    try:
        # Start a new conversation
        response = client.start_conversation(question)
        conversation_id = response.conversation_id
        message_id = response.message_id
        
        # Wait for the message to complete
        complete_message = client.wait_for_message_completion(conversation_id, message_id)
        
        # Process the response
        result, query_text = process_genie_response(client, conversation_id, message_id, complete_message)
        
        return conversation_id, result, query_text
        
    except Exception as e:
        return None, f"Sorry, an error occurred: {str(e)}. Please try again.", None

def continue_conversation(conversation_id: str, question: str) -> Tuple[Union[str, pd.DataFrame], Optional[str]]:
    """
    Send a follow-up message in an existing conversation.
    
    Args:
        conversation_id: The existing conversation ID
        question: The follow-up question
        
    Returns:
        Tuple containing:
        - response: Either text or DataFrame response
        - query_text: SQL query text if applicable, otherwise None
    """
    logger.info(f"Continuing conversation {conversation_id} with question: {question[:30]}...")
    
    client = GenieClient(
        host=DATABRICKS_HOST,
        space_id=SPACE_ID
    )
    
    try:
        # Send follow-up message in existing conversation
        response = client.send_message(conversation_id, question)
        message_id = response.message_id
        
        # Wait for the message to complete
        complete_message = client.wait_for_message_completion(conversation_id, message_id)
        
        # Process the response
        result, query_text = process_genie_response(client, conversation_id, message_id, complete_message)
        
        return result, query_text
        
    except Exception as e:
        # Handle specific errors
        if "429" in str(e) or "Too Many Requests" in str(e):
            return "Sorry, the system is currently experiencing high demand. Please try again in a few moments.", None
        elif "Conversation not found" in str(e):
            return "Sorry, the previous conversation has expired. Please try your query again to start a new conversation.", None
        else:
            logger.error(f"Error continuing conversation: {str(e)}")
            return f"Sorry, an error occurred: {str(e)}", None

def process_genie_response(
    client: GenieClient,
    conversation_id: str,
    message_id: str,
    complete_message: GenieMessage,
) -> Tuple[Union[str, pd.DataFrame], Optional[str]]:
    """
    Process the response from Genie
    
    Args:
        client: The GenieClient instance
        conversation_id: The conversation ID
        message_id: The message ID
        complete_message: The completed message response
        
    Returns:
        Tuple containing:
        - result: Either text or DataFrame response
        - query_text: SQL query text if applicable, otherwise None
    """
    # Check attachments first
    attachments = complete_message.attachments or []
    for attachment in attachments:
        attachment_id = attachment.attachment_id

        # If there's text content in the attachment, return it
        if attachment.text and attachment.text.content:
            return attachment.text.content, None

        # If there's a query, get the result
        if attachment.query:
            query_text = attachment.query.query or ""
            if not attachment_id:
                continue

            query_result = client.get_query_result(conversation_id, message_id, attachment_id)

            data_array = query_result.get("data_array", [])
            schema = query_result.get("schema", {})
            columns = [col.get("name") for col in schema.get("columns", [])]

            # If we have data, return as DataFrame
            if data_array:
                # If no columns from schema, create generic ones
                if not columns and data_array and len(data_array) > 0:
                    columns = [f"column_{i}" for i in range(len(data_array[0]))]

                df = pd.DataFrame(data_array, columns=columns)
                return df, query_text

    # If no attachments or no data in attachments, return text content
    if complete_message.content is not None:
        return complete_message.content, None

    return "No response available", None

def genie_query(question: str) -> Union[Tuple[str, Optional[str]], Tuple[pd.DataFrame, str]]:
    """
    Main entry point for querying Genie.
    
    Args:
        question: The question to ask
        
    Returns:
        Tuple containing either:
        - (text_response, None) for text responses
        - (dataframe, sql_query) for data responses
    """
    try:
        # Start a new conversation for each query
        conversation_id, result, query_text = start_new_conversation(question)
        return result, query_text
            
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}. Please try again.")
        return f"Sorry, an error occurred: {str(e)}. Please try again.", None