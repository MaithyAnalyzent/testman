import asyncio
import logging
from datetime import datetime, timezone
import random
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, List, Optional
import json

logger = logging.getLogger("mental_health_model")
logging.basicConfig(level=logging.INFO)

class ContentManager:
    """Manages different types of mental health content and topics"""
    
    def __init__(self):
        self.topics = {
            'stress_management': {
                'subtopics': [
                    'progressive muscle relaxation',
                    'breathing techniques',
                    'stress hormones',
                    'workplace stress',
                    'academic stress',
                    'physical symptoms of stress'
                ],
                'key_terms': ['cortisol', 'adrenaline', 'relaxation', 'coping']
            },
            'mindfulness': {
                'subtopics': [
                    'body scan meditation',
                    'mindful walking',
                    'present moment awareness',
                    'mindful eating',
                    'meditation science',
                    'neuroplasticity'
                ],
                'key_terms': ['awareness', 'presence', 'meditation', 'focus']
            },
            'mental_health_facts': {
                'subtopics': [
                    'common misconceptions',
                    'stigma reduction',
                    'mental health statistics',
                    'latest research',
                    'treatment options',
                    'brain chemistry'
                ],
                'key_terms': ['research', 'facts', 'studies', 'science']
            },
            'self_care': {
                'subtopics': [
                    'daily routines',
                    'emotional boundaries',
                    'digital wellbeing',
                    'creative expression',
                    'nature connection',
                    'social connections'
                ],
                'key_terms': ['routine', 'boundaries', 'wellness', 'care']
            },
            'anxiety_depression': {
                'subtopics': [
                    'anxiety management',
                    'depression coping',
                    'panic attacks',
                    'mood tracking',
                    'therapy types',
                    'medication facts'
                ],
                'key_terms': ['anxiety', 'depression', 'panic', 'therapy']
            },
            'sleep_health': {
                'subtopics': [
                    'sleep hygiene',
                    'circadian rhythm',
                    'sleep disorders',
                    'bedtime routines',
                    'sleep science',
                    'dream psychology'
                ],
                'key_terms': ['sleep', 'rest', 'insomnia', 'dreams']
            },
            'nutrition_mental_health': {
                'subtopics': [
                    'gut-brain connection',
                    'mood-boosting foods',
                    'nutritional psychiatry',
                    'hydration impact',
                    'eating patterns',
                    'supplements research'
                ],
                'key_terms': ['nutrition', 'diet', 'food', 'gut health']
            }
        }

        # Track topic usage to ensure variety
        self.topic_usage = {topic: 0 for topic in self.topics.keys()}
        
    def get_next_topic(self) -> tuple:
        """Get the least recently used topic and a random subtopic"""
        # Get topic with lowest usage
        topic = min(self.topic_usage.items(), key=lambda x: x[1])[0]
        subtopic = random.choice(self.topics[topic]['subtopics'])
        
        # Update usage counter
        self.topic_usage[topic] += 1
        
        return topic, subtopic

class MentalHealthPostingModel:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.last_post_time = None
        self.content_manager = ContentManager()
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            api_key=bot_instance.settings.GROQ_API_KEY,
            model_name="mixtral-8x7b-32768"
        )
        
        # Load post templates
        self.templates = {
            'educational': [
                "mental health facts bestie! {content} 🧠 science said that fr! {hashtags}",
                "therapy tea time: {content} no cap, research proves it! {hashtags}",
                "bestie did u know? {content} this is your sign to level up 💫 {hashtags}"
            ],
            'tips': [
                "mental health hack alert! {content} trust me on this one fr {hashtags}",
                "bestie try this rn: {content} it's giving self-care energy ✨ {hashtags}",
                "your daily reminder: {content} you got this fr fr {hashtags}"
            ],
            'research': [
                "new study just dropped! {content} science is wild fr {hashtags}",
                "research tea: {content} let that sink in bestie 🤯 {hashtags}",
                "mental health news flash: {content} sharing facts only! {hashtags}"
            ]
        }

    async def generate_content(self) -> Dict:
        """Generate varied mental health content with context-aware formatting"""
        try:
            # Get next topic and subtopic
            topic, subtopic = self.content_manager.get_next_topic()
            
            # Generate content using LLM
            content = await self._generate_llm_content(topic, subtopic)
            if not content:
                return None
            
            # Generate relevant hashtags
            hashtags = await self._generate_hashtags(topic, subtopic)
            
            # Select appropriate template
            template_type = self._get_template_type(topic)
            template = random.choice(self.templates[template_type])
            
            # Format post
            post_text = template.format(
                content=content,
                hashtags=' '.join(hashtags)
            )
            
            # Ensure post length
            if len(post_text) > 280:
                post_text = post_text[:277] + "..."
            
            return {
                'text': post_text,
                'topic': topic,
                'subtopic': subtopic
            }
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return None

    async def _generate_llm_content(self, topic: str, subtopic: str) -> str:
        """Generate informative content using Groq LLM"""
        try:
            system_prompt = """You are Therapy Punch, a Gen-Z mental health advocate and expert.
            You combine professional mental health knowledge with Gen-Z slang while maintaining accuracy.
            Keep responses engaging, informative, and authentic to Gen-Z voice."""
            
            user_prompt = f"""Topic: {topic} - {subtopic}
            
            Create an informative mental health post that:
            1. Shares a specific insight or fact about {subtopic}
            2. Connects it to practical mental health benefits
            3. Provides an actionable tip
            4. Uses authentic Gen-Z language naturally
            5. Stays under 150 characters (to leave room for template and hashtags)
            
            Make it engaging and memorable!"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.agenerate([messages])
            if response and hasattr(response, 'generations') and response.generations:
                generated_text = response.generations[0][0].text
                return generated_text.strip()
            return None

        except Exception as e:
            logger.error(f"LLM content generation error: {e}")
            return None

    async def _generate_hashtags(self, topic: str, subtopic: str) -> List[str]:
        """Generate relevant hashtags based on topic and subtopic"""
        try:
            # First try topic-specific hashtags from content manager
            base_tags = ['MentalHealth', 'TherapyPunch', 'Healing']
            topic_terms = self.content_manager.topics[topic]['key_terms']
            topic_tags = [f"#{term.title().replace(' ', '')}" for term in topic_terms[:2]]
            
            # Try to get additional hashtags from LLM
            prompt = f"""Topic: {topic} - {subtopic}
            Generate 2 trendy, relevant hashtags for this mental health topic.
            Return only the hashtags without # symbol, separated by spaces.
            Example: MentalHealthAwareness WellnessJourney"""
            
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.agenerate([messages])
            
            if response and hasattr(response, 'generations') and response.generations:
                llm_tags = response.generations[0][0].text.strip().split()
                llm_tags = [f"#{tag}" for tag in llm_tags[:2]]
                
                # Combine all tags and take unique ones
                all_tags = list(set(base_tags + topic_tags + llm_tags))
                return all_tags[:4]
                
            return base_tags + topic_tags[:2]

        except Exception as e:
            logger.error(f"Hashtag generation error: {e}")
            return base_tags

    def _get_template_type(self, topic: str) -> str:
        """Determine appropriate template type based on topic"""
        educational_topics = ['mental_health_facts', 'nutrition_mental_health']
        research_topics = ['sleep_health', 'anxiety_depression']
        
        if topic in educational_topics:
            return 'educational'
        elif topic in research_topics:
            return 'research'
        return 'tips'

    def can_post(self) -> bool:
        """Check if enough time has passed since last post"""
        if not self.last_post_time:
            return True
        
        time_diff = (datetime.now() - self.last_post_time).total_seconds()
        return time_diff >= 1800  # 30 minutes between posts

    async def post_content(self) -> bool:
        """Generate and post content"""
        try:
            if not self.can_post():
                return False
            
            content = await self.generate_content()
            if not content:
                return False
            
            success = await self.create_post(content)
            if success:
                self.last_post_time = datetime.now()
                logger.info(f"Successfully posted about {content['topic']} - {content['subtopic']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Posting error: {e}")
            return False

    async def create_post(self, content: Dict) -> bool:
        """Create a post with the generated content"""
        try:
            created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            post_record = {
                'text': content['text'],
                'createdAt': created_at
            }
            
            response = self.bot.client.com.atproto.repo.create_record({
                'repo': self.bot.settings.BLUESKY_HANDLE,
                'collection': 'app.bsky.feed.post',
                'record': post_record
            })
            
            return bool(response)
            
        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return False

    async def run(self):
        """Main posting loop"""
        while True:
            try:
                await self.post_content()
                await asyncio.sleep(300)  # Wait 30 minutes between posts
                
            except Exception as e:
                logger.error(f"Run loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on err