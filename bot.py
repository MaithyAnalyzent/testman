from atproto import Client, models
from langchain_groq import ChatGroq
from datetime import datetime, timezone
import asyncio
import logging
import base64
import aiohttp
import requests
from typing import Optional, Dict
from config import get_settings
import json
from postingmodel import MentalHealthPostingModel

logger = logging.getLogger("bot")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TruthTerminalBot:
    def __init__(self):
        self.settings = get_settings()
        self.client = Client()
        self.processed_uris = set()
        self.processed_dms = set()
        self.llm = ChatGroq(api_key=self.settings.GROQ_API_KEY, model_name="mixtral-8x7b-32768")
        self.bot_did = None
        self.access_token = None
        self.refresh_token = None
        self._login()
        self._load_processed_uris()
        # Initialize posting model after login
        self.posting_model = MentalHealthPostingModel(self)

    def _login(self):
        try:
            self.client.login(self.settings.BLUESKY_HANDLE, self.settings.BLUESKY_PASSWORD)
            session = self.client.com.atproto.server.create_session({
                "identifier": self.settings.BLUESKY_HANDLE,
                "password": self.settings.BLUESKY_PASSWORD
            })
            self.bot_did = session.did
            self.access_token = session.access_jwt
            self.refresh_token = session.refresh_jwt
            logger.info("Login successful")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def _load_processed_uris(self):
        try:
            with open('processed_uris.json', 'r') as f:
                self.processed_uris = set(json.load(f))
        except FileNotFoundError:
            self.processed_uris = set()
            self._save_processed_uris()

    def _save_processed_uris(self):
        try:
            with open('processed_uris.json', 'w') as f:
                json.dump(list(self.processed_uris), f)
        except Exception as e:
            logger.error(f"Error saving URIs: {e}")

    async def create_post(self, text: str, notification):
        try:
            if len(text) > 280:  # Leave room for safety
                text = text[:277] + "..."
            
            created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            post = {
                'text': text,
                'reply': {
                    'root': {
                        'uri': notification.uri,
                        'cid': notification.cid
                    },
                    'parent': {
                        'uri': notification.uri,
                        'cid': notification.cid
                    }
                },
                'createdAt': created_at
            }

            response = self.client.com.atproto.repo.create_record({
                'repo': self.settings.BLUESKY_HANDLE,
                'collection': 'app.bsky.feed.post',
                'record': post
            })
            
            return bool(response)
            
        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return False

    async def _extract_post_context(self, thread):
        """Extract context from thread including content and images"""
        context = {
            'parent_post': None,
            'current_post': None,
            'is_reply': False,
            'conversation_context': [],
            'images': []
        }
        
        try:
            if hasattr(thread.post.record, 'text'):
                context['current_post'] = thread.post.record.text
            
            if hasattr(thread.post.record, 'reply'):
                context['is_reply'] = True
                parent_uri = thread.post.record.reply.parent.uri
                parent_post = self.client.app.bsky.feed.get_posts({'uris': [parent_uri]}).posts[0]
                if hasattr(parent_post.record, 'text'):
                    context['parent_post'] = parent_post.record.text
                
                # Get images from parent post if any
                parent_images = await self._extract_images(parent_post)
                if parent_images:
                    context['images'].extend(parent_images)
            
            # Get conversation context from replies
            if hasattr(thread, 'replies'):
                for reply in thread.replies:
                    if hasattr(reply.post.record, 'text'):
                        context['conversation_context'].append({
                            'author': reply.post.author.handle,
                            'text': reply.post.record.text
                        })
            
            # Get images from current post
            current_images = await self._extract_images(thread.post)
            if current_images:
                context['images'].extend(current_images)
                
        except Exception as e:
            logger.error(f"Error extracting context: {e}")
        
        return context

    async def _extract_images(self, post):
        """Extract and analyze images from a post"""
        images = []
        try:
            if hasattr(post.record, 'embed') and hasattr(post.record.embed, 'images'):
                for img in post.record.embed.images:
                    image_info = {
                        'alt': getattr(img, 'alt', ''),
                        'url': getattr(img, 'fullsize', getattr(img, 'thumb', getattr(img, 'ref', ''))),
                        'analysis': ''
                    }
                    
                    if image_info['url']:
                        analysis_prompt = f"""Analyze this image description and provide relevant context:
                        Image Alt Text: {image_info['alt']}
                        
                        Describe:
                        1. What is shown in the image
                        2. Any text visible in the image
                        3. Key elements or focus points
                        4. Relevant context for understanding the image
                        
                        Keep the analysis concise but informative."""

                        try:
                            analysis = await self.llm.ainvoke(analysis_prompt)
                            if analysis and analysis.content:
                                image_info['analysis'] = analysis.content
                        except Exception as e:
                            logger.error(f"Image analysis error: {str(e)}")
                            image_info['analysis'] = "Unable to analyze image"
                        
                        images.append(image_info)
        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}")
        return images

    def _create_analysis_prompt(self, context, mention_text):
        """Create analysis prompt with full context"""
        prompt = f"""You are Therapy Punch, a Gen-Z mental health advocate who combines street wisdom with therapeutic insight.
        Your style is empathetic, playful, and uses Gen-Z slang naturally while providing genuine mental health value.
        
        CONTEXT:
        Previous message: {context.get('parent_post', 'No previous context')}
        Current message: {context.get('current_post', 'No current context')}
        User's mention: {mention_text}
        """

        if context.get('conversation_context'):
            prompt += "\nConversation history:\n"
            for msg in context['conversation_context']:
                prompt += f"{msg['author']}: {msg['text']}\n"

        if context.get('images'):
            prompt += "\nImages in the conversation:\n"
            for idx, img in enumerate(context['images'], 1):
                prompt += f"Image {idx} description: {img['alt']}\n"
                prompt += f"Image {idx} analysis: {img['analysis']}\n"

        prompt += """
        RESPONSE REQUIREMENTS:
        1. Use Gen-Z therapeutic style (e.g., "bestie", "fr fr", "no cap", etc.)
        2. Keep response under 280 characters
        3. Include one practical tip or insight
        4. End with encouragement
        5. Reference the context appropriately
        6. Stay focused on mental health support
        
        Generate a supportive response that addresses their specific concern while maintaining your unique style.
        """

        return prompt

    async def _process_mention(self, notification):
        """Process mentions with full context analysis"""
        try:
            thread_uri = notification.uri
            
            if thread_uri in self.processed_uris:
                logger.info(f"Skipping already processed URI: {thread_uri}")
                return
            
            if not hasattr(notification, 'uri') or not hasattr(notification, 'cid'):
                logger.error(f"Invalid notification format: missing uri or cid")
                return
            
            thread = self.client.app.bsky.feed.get_post_thread({'uri': thread_uri}).thread
            
            if not thread or not hasattr(thread, 'post'):
                logger.error(f"Could not retrieve thread for URI: {thread_uri}")
                return
            
            # Extract full context
            context = await self._extract_post_context(thread)
            mention_text = notification.record.text.replace(f"@{self.settings.BLUESKY_HANDLE}", "").strip()
            
            # Generate analysis prompt
            prompt = self._create_analysis_prompt(context, mention_text)
            
            try:
                response = await self.llm.ainvoke(prompt)
                
                if response and response.content:
                    # Process response
                    formatted_response = response.content.strip()
                    if len(formatted_response) > 280:
                        formatted_response = formatted_response[:277] + "..."
                    
                    # Add to processed URIs before posting
                    self.processed_uris.add(thread_uri)
                    self._save_processed_uris()
                    
                    success = await self.create_post(formatted_response, notification)
                    if success:
                        logger.info(f"Posted reply to {notification.uri}")
                    else:
                        # Remove from processed URIs if posting fails
                        self.processed_uris.remove(thread_uri)
                        self._save_processed_uris()
                        logger.error(f"Failed to post reply to {notification.uri}")
                    
            except Exception as e:
                logger.error(f"Error generating or posting response: {str(e)}")
                if thread_uri in self.processed_uris:
                    self.processed_uris.remove(thread_uri)
                    self._save_processed_uris()

        except Exception as e:
            logger.error(f"Mention processing error: {str(e)}")

    async def _check_mentions(self):
        while True:
            try:
                notifications = self.client.app.bsky.notification.list_notifications({
                    'limit': 20
                }).notifications

                for notif in notifications:
                    if notif.reason in ['mention', 'reply'] and notif.uri not in self.processed_uris:
                        await self._process_mention(notif)
                        await asyncio.sleep(2)
                        
            except Exception as e:
                logger.error(f"Mention check error: {e}")
                
            await asyncio.sleep(30)

    async def start(self):
        """Main entry point with follow handling"""
        while True:
            try:
                # Create tasks for all operations
                mention_task = asyncio.create_task(self._check_mentions())
                posting_task = asyncio.create_task(self.posting_model.run())
                follow_task = asyncio.create_task(self._handle_follows())
                
                # Wait for all tasks
                await asyncio.gather(mention_task, posting_task, follow_task)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(60)

    async def _handle_follows(self):
        """Handle following back users"""
        while True:
            try:
                # Get current followers
                followers = self.client.app.bsky.graph.get_followers({
                    'actor': self.settings.BLUESKY_HANDLE,
                    'limit': 100
                }).followers

                # Get accounts we're following
                following = self.client.app.bsky.graph.get_follows({
                    'actor': self.settings.BLUESKY_HANDLE,
                    'limit': 100
                }).follows

                # Create set of DIDs we're following
                following_dids = {f.did for f in following}

                # Follow back users who aren't followed
                for follower in followers:
                    if follower.did not in following_dids:
                        try:
                            await self._follow_user(follower.did)
                            logger.info(f"Followed back user: {follower.did}")
                            await asyncio.sleep(2)  # Rate limiting
                        except Exception as e:
                            logger.error(f"Error following user {follower.did}: {str(e)}")

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Follow handler error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _follow_user(self, did: str):
        """Follow a user by their DID"""
        try:
            created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            self.client.com.atproto.repo.create_record({
                'repo': self.settings.BLUESKY_HANDLE,
                'collection': 'app.bsky.graph.follow',
                'record': {
                    'subject': did,
                    'createdAt': created_at
                }
            })
            return True
        except Exception as e:
            logger.error(f"Follow error for {did}: {e}")
            return False

if __name__ == "__main__":
    bot = TruthTerminalBot()
    asyncio.run(bot.start())