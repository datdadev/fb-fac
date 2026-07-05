"""
AI Analysis Module using Google Gemini API
Analyzes Facebook posts for 3D printing relevance
"""

import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_AI = os.getenv("USE_AI", "true").lower() == "true"

class AIAnalyzer:
    """AI Analyzer using Google Gemini API"""
    
    def __init__(self, api_key=None):
        """Initialize AI Analyzer"""
        self.api_key = api_key or GEMINI_API_KEY
        self.available = False
        self.model = None
        
        if not self.api_key:
            print("[AI] ⚠️ GEMINI_API_KEY not found. AI features disabled.")
            return
        
        try:
            # Try to import google-generativeai
            import google.generativeai as genai
            
            # Configure
            genai.configure(api_key=self.api_key)
            
            # Use the latest available model
            try:
                # Try gemini-2.0-flash-exp (latest)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except:
                try:
                    # Fallback to gemini-1.5-flash
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    try:
                        # Fallback to gemini-pro
                        self.model = genai.GenerativeModel('gemini-pro')
                    except:
                        # Check available models
                        available_models = [m.name for m in genai.list_models()]
                        print(f"[AI] Available models: {available_models}")
                        
                        # Use any gemini model
                        for model_name in available_models:
                            if 'gemini' in model_name:
                                self.model = genai.GenerativeModel(model_name)
                                break
            
            if self.model:
                self.available = True
                print(f"[AI] ✅ Gemini initialized with model: {self.model.model_name}")
            else:
                print("[AI] ❌ Could not find a suitable Gemini model")
                
        except ImportError:
            print("[AI] ⚠️ google-generativeai not installed. Install with: pip install google-generativeai")
        except Exception as e:
            print(f"[AI] ❌ Error initializing Gemini: {e}")
    
    def analyze_post(self, post_text, post_author=None, keywords_matched=None):
        """
        Analyze a Facebook post using AI
        
        Args:
            post_text: Content of the post
            post_author: Author of the post
            keywords_matched: Keywords that matched
        
        Returns:
            dict: Analysis result with reasoning, relevance, and recommendation
        """
        if not self.available or not USE_AI:
            return {
                'analysis': 'AI analysis disabled',
                'relevance_score': 1.0,
                'recommendation': 'contact',
                'reasoning': 'AI analysis disabled'
            }
        
        if not post_text or len(post_text.strip()) < 10:
            return {
                'analysis': 'Post content too short',
                'relevance_score': 0,
                'recommendation': 'skip',
                'reasoning': 'Content too short to analyze'
            }
        
        try:
            # Build prompt
            prompt = f"""
            Analyze this Facebook post for 3D printing service relevance.
            
            Post Content: "{post_text[:1000]}"
            Author: {post_author or 'Unknown'}
            Keywords matched: {', '.join(keywords_matched) if keywords_matched else 'None'}
            
            Evaluate if this post represents a genuine request for 3D printing services.
            
            Consider:
            1. Is the user actively seeking 3D printing services?
            2. Do they have a specific project/need?
            3. Are they asking for quotes or recommendations?
            4. Is this a legitimate business opportunity?
            5. Would our 3D printing service be suitable for their needs?
            
            Respond in JSON format with these fields:
            {{
                "is_relevant": true/false,
                "relevance_score": 0-1,
                "reasoning": "brief explanation",
                "recommendation": "contact" | "review" | "skip",
                "service_needed": "what 3D printing service they need",
                "urgency": "high" | "medium" | "low",
                "suggested_response": "recommended reply template"
            }}
            
            Return ONLY valid JSON, no other text.
            """
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse response
            if response and response.text:
                try:
                    result = json.loads(response.text.strip())
                    return result
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            return result
                        except:
                            pass
                    
                    # Fallback: return raw text
                    return {
                        'analysis': response.text[:500],
                        'relevance_score': 0.5,
                        'recommendation': 'review',
                        'reasoning': 'Could not parse AI response'
                    }
            else:
                return {
                    'analysis': 'No response from AI',
                    'relevance_score': 0,
                    'recommendation': 'skip',
                    'reasoning': 'AI returned empty response'
                }
                
        except Exception as e:
            print(f"[AI] ❌ Error: {e}")
            return {
                'analysis': f'AI analysis error: {str(e)[:100]}',
                'relevance_score': 0,
                'recommendation': 'review',
                'reasoning': 'Technical error during analysis'
            }
    
    def analyze_batch(self, posts):
        """
        Analyze multiple posts in batch
        
        Args:
            posts: List of post dictionaries
        
        Returns:
            List of posts with analysis added
        """
        if not self.available or not USE_AI:
            for post in posts:
                post['analysis'] = 'AI analysis disabled'
                post['relevance_score'] = 1.0
                post['recommendation'] = 'contact'
            return posts
        
        analyzed_posts = []
        
        for post in posts:
            print(f"[AI] Analyzing post from {post.get('author', 'Unknown')}...")
            
            # Analyze
            analysis = self.analyze_post(
                post.get('text', ''),
                post.get('author'),
                post.get('keyword_matched', [])
            )
            
            # Merge analysis into post
            post['analysis'] = analysis.get('analysis', 'No analysis')
            post['relevance_score'] = analysis.get('relevance_score', 0)
            post['recommendation'] = analysis.get('recommendation', 'review')
            post['reasoning'] = analysis.get('reasoning', '')
            post['service_needed'] = analysis.get('service_needed', '')
            post['urgency'] = analysis.get('urgency', 'medium')
            post['suggested_response'] = analysis.get('suggested_response', '')
            post['is_relevant'] = analysis.get('is_relevant', False)
            
            analyzed_posts.append(post)
            
            # Avoid rate limiting
            time.sleep(1)
        
        return analyzed_posts

# For testing
if __name__ == "__main__":
    print("="*60)
    print("🤖 AI ANALYZER TEST")
    print("="*60)
    
    # Test posts
    test_posts = [
        {
            'text': 'Tôi cần tìm đơn vị in 3D uy tín để in mô hình kiến trúc. Ai biết chỗ nào tốt chỉ mình với ạ.',
            'author': 'Nguyen Van A',
            'keyword_matched': ['cần in 3D', 'dịch vụ in 3D']
        },
        {
            'text': 'Bán đồ chơi cũ giá rẻ, không liên quan gì đến in 3D.',
            'author': 'Tran Van B',
            'keyword_matched': ['in 3D']
        }
    ]
    
    analyzer = AIAnalyzer()
    
    if analyzer.available:
        for post in test_posts:
            print(f"\n📝 Post: {post['text'][:50]}...")
            result = analyzer.analyze_post(post['text'], post['author'], post['keyword_matched'])
            print(f"  Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("❌ AI not available. Please set GEMINI_API_KEY in .env")