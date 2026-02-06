"""Instagram uploader using Graph API."""

import os
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


def upload_to_instagram(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: Dict
) -> Optional[str]:
    """
    Upload video to Instagram Reels using Graph API.
    
    Args:
        video_path: Path to video file
        caption: Video caption
        hashtags: List of hashtags
        credentials: Instagram API credentials (access_token, ig_user_id)
        
    Returns:
        Media ID if successful, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Uploading to Instagram Reels")
    
    # Get credentials
    access_token = credentials.get("access_token") or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = credentials.get("ig_user_id") or os.getenv("INSTAGRAM_USER_ID")
    
    if not access_token or not ig_user_id:
        logger.error("Instagram credentials not provided")
        raise ValueError("Instagram access token and user ID required. "
                        "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID environment variables.")
    
    try:
        import requests
        
        # Prepare caption with hashtags
        full_caption = f"{caption}\n\n{' '.join(hashtags)}"
        
        # Instagram Graph API base URL
        base_url = f"https://graph.instagram.com/v18.0/{ig_user_id}"
        
        # Instagram Graph API requires video to be hosted on publicly accessible URL
        # This is a limitation of the Instagram API - videos must be accessible via HTTP(S)
        video_url = credentials.get("video_url")
        
        if not video_url:
            logger.warning("Instagram upload requires video to be hosted on a publicly accessible URL")
            logger.warning("For production deployment:")
            logger.warning("  1. Upload video file to CDN (AWS S3, Cloudflare, etc.)")
            logger.warning("  2. Provide the public URL in credentials['video_url']")
            logger.warning("  3. Re-run upload with the hosted URL")
            logger.info("Skipping Instagram upload - video not hosted")
            return None
        
        # Step 1: Create media container
        container_endpoint = f"{base_url}/media"
        
        container_params = {
            "access_token": access_token,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": full_caption[:2200],  # Instagram caption limit
            "share_to_feed": True
        }
        
        logger.info("Creating Instagram media container")
        response = requests.post(container_endpoint, params=container_params)
        
        if response.status_code != 200:
            logger.error(f"Failed to create container: {response.status_code} {response.text}")
            return None
        
        container_data = response.json()
        container_id = container_data.get("id")
        
        if not container_id:
            logger.error("No container ID received from Instagram")
            return None
        
        logger.info(f"Media container created: {container_id}")
        
        # Step 2: Wait for container to be ready
        if not check_instagram_container_status(container_id, access_token):
            logger.error("Container processing failed or timed out")
            return None
        
        # Step 3: Publish the media
        publish_endpoint = f"{base_url}/media_publish"
        publish_params = {
            "access_token": access_token,
            "creation_id": container_id
        }
        
        logger.info("Publishing Instagram Reel")
        publish_response = requests.post(publish_endpoint, params=publish_params)
        
        if publish_response.status_code != 200:
            logger.error(f"Failed to publish: {publish_response.status_code} {publish_response.text}")
            return None
        
        publish_data = publish_response.json()
        media_id = publish_data.get("id")
        
        logger.info(f"Instagram Reel published: {media_id}")
        return media_id
        
    except ImportError:
        logger.error("requests library not available")
        logger.warning("Instagram upload skipped - install requests library")
        return None
    except Exception as e:
        logger.error(f"Instagram upload failed: {str(e)}")
        return None


def check_instagram_container_status(
    container_id: str,
    access_token: str,
    max_wait: int = 300
) -> bool:
    """
    Check Instagram media container status.
    
    Args:
        container_id: Media container ID
        access_token: Instagram access token
        max_wait: Maximum wait time in seconds
        
    Returns:
        True if ready, False if failed or timeout
    """
    import requests
    
    endpoint = f"https://graph.instagram.com/v18.0/{container_id}"
    params = {
        "access_token": access_token,
        "fields": "status_code"
    }
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(endpoint, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to check container status: {response.text}")
            return False
        
        data = response.json()
        status = data.get("status_code")
        
        if status == "FINISHED":
            return True
        elif status == "ERROR":
            logger.error("Container processing failed")
            return False
        
        # Wait before checking again
        time.sleep(5)
    
    logger.error("Timeout waiting for container to be ready")
    return False
