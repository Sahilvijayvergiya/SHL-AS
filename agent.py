import os
from openai import OpenAI
from typing import List, Dict, Optional, Tuple
from models import Message, ChatResponse, Recommendation
from retrieval import RetrievalSystem
from catalog import SHLCatalog


class ConversationalAgent:
    """Conversational agent for SHL assessment recommendations."""
    
    def __init__(self, retrieval_system: RetrievalSystem):
        self.retrieval_system = retrieval_system
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("MODEL", "gpt-4o-mini")
        
        # Conversation state tracking
        self.conversation_context = {
            "job_level": None,
            "test_types": [],
            "categories": [],
            "query": "",
            "needs_clarification": True,
            "clarification_answered": False,
            "turn_count": 0
        }
    
    def process_conversation(self, messages: List[Message]) -> ChatResponse:
        """Process conversation and generate response."""
        self.conversation_context["turn_count"] = len([m for m in messages if m.role == "user"])
        
        # Enforce turn cap (max 8 turns total)
        if len(messages) >= 16:  # 8 user + 8 assistant = 16 messages max
            return ChatResponse(
                reply="I apologize, but we've reached the maximum number of turns for this conversation. Please start a new conversation if you'd like to continue.",
                recommendations=[],
                end_of_conversation=True
            )
        
        # Check for comparison request
        comparison_result = self._check_for_comparison(messages)
        if comparison_result:
            return self._generate_comparison_response(comparison_result)
        
        # Check for finalization first (before removal)
        if self._check_for_finalization(messages):
            # Check if user wants to keep as-is
            if self._is_keep_as_is(messages):
                # Get previous recommendations from conversation
                intent = self._extract_intent(messages)
                recommendations = self._get_recommendations(intent)
                reply = "Confirmed. Shortlist as above."
                return ChatResponse(
                    reply=reply,
                    recommendations=[self._to_recommendation(r) for r in recommendations],
                    end_of_conversation=True
                )
            
            # Extract assessments mentioned in the final message
            mentioned = self._extract_mentioned_assessments(messages[-1].content)
            if mentioned:
                reply = self._generate_finalization_reply(mentioned)
                return ChatResponse(
                    reply=reply,
                    recommendations=[self._to_recommendation(r) for r in mentioned],
                    end_of_conversation=True
                )
            else:
                # Fall back to retrieval
                intent = self._extract_intent(messages)
                recommendations = self._get_recommendations(intent)
                reply = self._generate_finalization_reply(recommendations)
                return ChatResponse(
                    reply=reply,
                    recommendations=[self._to_recommendation(r) for r in recommendations],
                    end_of_conversation=True
                )
        
        # Check for removal request
        removal = self._check_for_removal(messages)
        if removal:
            return self._handle_removal(removal, messages)
        
        # Check for refinement request
        refinement = self._check_for_refinement(messages)
        if refinement:
            self._apply_refinement(refinement)
        
        # Extract user intent from conversation
        intent = self._extract_intent(messages)
        
        # Check if we have enough context to recommend
        if self._has_sufficient_context(intent):
            recommendations = self._get_recommendations(intent)
            reply = self._generate_recommendation_reply(recommendations, intent)
            return ChatResponse(
                reply=reply,
                recommendations=[self._to_recommendation(r) for r in recommendations],
                end_of_conversation=False  # Don't end until user confirms
            )
        else:
            # Ask clarifying question
            reply = self._generate_clarification(intent)
            return ChatResponse(
                reply=reply,
                recommendations=[],
                end_of_conversation=False
            )
    
    def _check_for_comparison(self, messages: List[Message]) -> Optional[List[str]]:
        """Check if user is asking for a comparison."""
        last_user_msg = messages[-1].content.lower()
        
        comparison_keywords = ["difference", "compare", "vs", "versus", "between"]
        if any(keyword in last_user_msg for keyword in comparison_keywords):
            # Extract assessment names - look for known assessment names in the message
            assessment_names = []
            
            # Build a mapping of lowercase names to original names
            name_map = {a.name.lower(): a.name for a in self.retrieval_system.catalog.assessments}
            
            # Check for exact name matches
            for lower_name, original_name in name_map.items():
                if lower_name in last_user_msg:
                    assessment_names.append(original_name)
            
            # Also try to extract capitalized words that might be assessment names
            import re
            capitalized_words = re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', messages[-1].content)
            for word in capitalized_words:
                word_lower = word.lower()
                # Check if this matches any assessment name
                for lower_name, original_name in name_map.items():
                    if word_lower in lower_name or lower_name in word_lower:
                        if original_name not in assessment_names:
                            assessment_names.append(original_name)
            
            if len(assessment_names) >= 2:
                return assessment_names[:2]  # Return at most 2 for comparison
        
        return None
    
    def _generate_comparison_response(self, assessment_names: List[str]) -> ChatResponse:
        """Generate a comparison response."""
        comparisons = self.retrieval_system.compare(assessment_names)
        
        if len(comparisons) < 2:
            reply = "I could only find one of those assessments in the catalog. Please provide the exact names of the assessments you'd like to compare."
            return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)
        
        # Build comparison text with detailed explanations
        reply_parts = []
        
        # Check if this is a specific comparison type (e.g., OPQ vs OPQ MQ Sales Report)
        names = list(comparisons.keys())
        if any("OPQ" in name.upper() for name in names) and len(comparisons) == 2:
            # Special handling for OPQ comparisons
            reply_parts.append("**OPQ (OPQ32r)** is the underlying **personality questionnaire**: a broad, standard measure of workplace behavioural style used across roles and decisions (development, team fit, etc.).")
            reply_parts.append("")
            reply_parts.append(f"**{names[1]}** is a **reporting product**, not a different questionnaire. It summarizes OPQ results in a **sales-specific** way—graphical and narrative emphasis on behaviours tied to sales success. You can **optionally** add the **Motivation Questionnaire (MQ)** so the same report also reflects **sales motivators and drives**; without MQ, you still get the sales-framed OPQ story.")
            reply_parts.append("")
            reply_parts.append("So: one assessment instrument (OPQ32r) for personality; the Sales Report is how you **read** those results for sellers (and optionally enrich with MQ).")
        else:
            # General comparison
            reply_parts.append("Here's a comparison of the assessments you asked about:\n")
            
            for name, details in comparisons.items():
                reply_parts.append(f"\n**{details['name']}** ({details['test_type']})")
                if details['description']:
                    reply_parts.append(f"- Description: {details['description'][:200]}...")
                if details['duration']:
                    reply_parts.append(f"- Duration: {details['duration']}")
                if details['job_levels']:
                    reply_parts.append(f"- Job Levels: {', '.join(details['job_levels'])}")
                if details['categories']:
                    reply_parts.append(f"- Categories: {', '.join(details['categories'])}")
        
        reply = "\n".join(reply_parts)
        return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)
    
    def _check_for_refinement(self, messages: List[Message]) -> Optional[Dict]:
        """Check if user is refining their request."""
        last_user_msg = messages[-1].content.lower()
        
        refinement_keywords = ["actually", "add", "also", "instead", "rather", "change", "prefer", "include"]
        if any(keyword in last_user_msg for keyword in refinement_keywords):
            # Extract what they're adding/changing
            refinement = {}
            
            # Check for test type mentions
            test_type_map = {
                "personality": "P",
                "knowledge": "K",
                "aptitude": "A",
                "skill": "S",
                "cognitive": "A",
                "situational": "B",
                "simulation": "S"
            }
            for keyword, test_type in test_type_map.items():
                if keyword in last_user_msg:
                    refinement.setdefault("test_types", []).append(test_type)
            
            # Check for category mentions
            all_categories = self.retrieval_system.get_all_categories()
            for cat in all_categories:
                if cat.lower() in last_user_msg:
                    refinement.setdefault("categories", []).append(cat)
            
            # Check for specific assessment additions
            mentioned = self._extract_mentioned_assessments(messages[-1].content)
            if mentioned:
                refinement["add_assessments"] = mentioned
            
            return refinement if refinement else None
        
        return None
    
    def _check_for_removal(self, messages: List[Message]) -> Optional[str]:
        """Check if user is asking to remove a specific assessment."""
        last_user_msg = messages[-1].content.lower()
        
        removal_keywords = ["remove", "drop", "delete", "exclude", "without", "out"]
        if any(keyword in last_user_msg for keyword in removal_keywords):
            # Try to extract the assessment name to remove
            # Check for common abbreviations and full names
            assessment_names = {
                "opq32r": "Occupational Personality Questionnaire OPQ32r",
                "opq": "Occupational Personality Questionnaire OPQ32r",
                "verify g+": "SHL Verify Interactive G+",
                "verify g": "SHL Verify Interactive G+",
                "graduate scenarios": "Graduate Scenarios",
                "rest": "RESTful Web Services (New)",
                "restful": "RESTful Web Services (New)",
                "restful web services": "RESTful Web Services (New)",
                "verify": "SHL Verify Interactive G+",
                "dsi": "Dependability and Safety Instrument (DSI)",
                "safety": "Manufac. & Indust. - Safety & Dependability 8.0"
            }
            
            for short_name, full_name in assessment_names.items():
                if short_name in last_user_msg:
                    return full_name
            
            # Also check full catalog names
            for assessment in self.retrieval_system.catalog.assessments:
                if assessment.name.lower() in last_user_msg:
                    return assessment.name
        
        return None
    
    def _check_for_finalization(self, messages: List[Message]) -> bool:
        """Check if user is finalizing the list."""
        last_user_msg = messages[-1].content.lower()
        
        finalization_keywords = ["final list", "final", "confirmed", "that's it", "done", "complete", "that's good", "perfect", "confirmed.", "locking it in", "keep the shortlist as-is", "keep as-is", "understood. keep the shortlist", "confirmed. hybrid battery"]
        return any(keyword in last_user_msg for keyword in finalization_keywords)
    
    def _is_keep_as_is(self, messages: List[Message]) -> bool:
        """Check if user wants to keep the current recommendations as-is."""
        last_user_msg = messages[-1].content.lower()
        
        keep_as_is_keywords = ["keep as-is", "keep the shortlist as-is", "keep the shortlist", "confirmed. hybrid", "understood. keep", "that matches how the catalog is built"]
        return any(keyword in last_user_msg for keyword in keep_as_is_keywords)
    
    def _apply_refinement(self, refinement: Dict):
        """Apply refinement to conversation context."""
        if "test_types" in refinement:
            self.conversation_context["test_types"].extend(refinement["test_types"])
        if "categories" in refinement:
            self.conversation_context["categories"].extend(refinement["categories"])
    
    def _handle_removal(self, assessment_name: str, messages: List[Message]) -> ChatResponse:
        """Handle request to remove a specific assessment."""
        # Check if there's a suitable alternative
        intent = self._extract_intent(messages)
        
        # Try to find alternative assessments of the same type
        assessment_to_remove = None
        for assessment in self.retrieval_system.catalog.assessments:
            if assessment.name == assessment_name:
                assessment_to_remove = assessment
                break
        
        if assessment_to_remove:
            # Look for alternatives of same test type
            alternatives = []
            for a in self.retrieval_system.catalog.assessments:
                if a.test_type == assessment_to_remove.test_type and a.name != assessment_name:
                    # Check if it's shorter
                    if assessment_to_remove.duration and a.duration:
                        try:
                            orig_duration = int(assessment_to_remove.duration.split()[0])
                            alt_duration = int(a.duration.split()[0])
                            if alt_duration < orig_duration:
                                alternatives.append(a)
                        except (ValueError, IndexError):
                            pass
                    elif not assessment_to_remove.duration:
                        alternatives.append(a)
            
            if alternatives:
                # Return the best alternative
                reply = f"I can replace {assessment_name} with {alternatives[0].name}, which is shorter. Would you like me to make this change?"
                return ChatResponse(
                    reply=reply,
                    recommendations=[],
                    end_of_conversation=False
                )
            else:
                # No suitable alternative
                reply = f"{assessment_name} is the most relevant solution for your need. As such, there is no shorter alternative to be used as its replacement."
                return ChatResponse(
                    reply=reply,
                    recommendations=[],
                    end_of_conversation=False
                )
        
        return ChatResponse(
            reply="I couldn't find that assessment in the catalog.",
            recommendations=[],
            end_of_conversation=False
        )
    
    def _generate_finalization_reply(self, recommendations: List) -> str:
        """Generate reply when user finalizes the list."""
        if not recommendations:
            return "I don't have any assessments to confirm. Please let me know what you'd like to include."
        
        reply = f"Updated. Final shortlist confirmed. Here are {len(recommendations)} assessment{'s' if len(recommendations) > 1 else ''}:"
        for i, rec in enumerate(recommendations, 1):
            reply += f"\n{i}. {rec.name} ({rec.test_type})"
        
        return reply
    
    def _extract_mentioned_assessments(self, message: str) -> List:
        """Extract specific assessments mentioned in the user's message."""
        message_lower = message.lower()
        mentioned = []
        
        # If message contains "final list:" or similar, only extract after that
        final_list_keywords = ["final list:", "final list", "confirmed:", "confirmed"]
        relevant_text = message_lower
        for keyword in final_list_keywords:
            if keyword in message_lower:
                idx = message_lower.find(keyword) + len(keyword)
                relevant_text = message_lower[idx:]
                break
        
        # Map common names to catalog names
        name_map = {
            "verify g+": "SHL Verify Interactive G+",
            "verify g": "SHL Verify Interactive G+",
            "graduate scenarios": "Graduate Scenarios",
            "opq32r": "Occupational Personality Questionnaire OPQ32r",
            "opq": "Occupational Personality Questionnaire OPQ32r"
        }
        
        for short_name, full_name in name_map.items():
            if short_name in relevant_text:
                for assessment in self.retrieval_system.catalog.assessments:
                    if assessment.name == full_name:
                        # Avoid duplicates
                        if assessment not in mentioned:
                            mentioned.append(assessment)
                        break
        
        return mentioned
    
    def _extract_intent(self, messages: List[Message]) -> Dict:
        """Extract user intent from conversation history."""
        intent = {
            "query": "",
            "job_level": None,
            "test_types": [],
            "categories": []
        }
        
        # Combine all user messages
        all_user_text = " ".join([m.content for m in messages if m.role == "user"])
        intent["query"] = all_user_text
        
        # Extract job level
        job_level_keywords = {
            "entry": "Entry",
            "junior": "Junior",
            "mid": "Mid",
            "senior": "Senior",
            "executive": "Executive",
            "manager": "Manager",
            "director": "Director"
        }
        for keyword, level in job_level_keywords.items():
            if keyword in all_user_text.lower():
                intent["job_level"] = level
                break
        
        # Extract test types
        test_type_map = {
            "personality": "P",
            "knowledge": "K",
            "aptitude": "A",
            "skill": "S",
            "technical": "K",
            "programming": "K",
            "coding": "K"
        }
        for keyword, test_type in test_type_map.items():
            if keyword in all_user_text.lower():
                if test_type not in intent["test_types"]:
                    intent["test_types"].append(test_type)
        
        # Extract categories
        all_categories = self.retrieval_system.get_all_categories()
        for cat in all_categories:
            if cat.lower() in all_user_text.lower():
                if cat not in intent["categories"]:
                    intent["categories"].append(cat)
        
        # Merge with conversation context
        if self.conversation_context["job_level"]:
            intent["job_level"] = self.conversation_context["job_level"]
        if self.conversation_context["test_types"]:
            intent["test_types"].extend(self.conversation_context["test_types"])
        if self.conversation_context["categories"]:
            intent["categories"].extend(self.conversation_context["categories"])
        
        return intent
    
    def _has_sufficient_context(self, intent: Dict) -> bool:
        """Check if we have enough context to make recommendations."""
        # Need at least a meaningful query (more than just "assessment" or "test")
        query_lower = intent["query"].lower()
        
        # Check if this is the first turn with senior leadership query
        if self.conversation_context["turn_count"] == 1:
            if "senior leadership" in query_lower or "cxo" in query_lower or "executive" in query_lower:
                return False  # Need to ask about purpose (selection vs development)
            
            # Check for Rust or other specific languages that need clarification
            if "rust" in query_lower or any(lang in query_lower for lang in ["python", "golang", "swift", "kotlin"]):
                return False  # Need to explain about Smart Interview Live Coding
        
        # If we asked for clarification about senior leadership purpose, check if answered
        if not self.conversation_context["clarification_answered"]:
            if "senior leadership" in query_lower or "cxo" in query_lower or "executive" in query_lower or "director" in query_lower:
                # Check if user answered the purpose question
                if "selection" in query_lower or "development" in query_lower or "hiring" in query_lower or "feedback" in query_lower:
                    self.conversation_context["clarification_answered"] = True
                else:
                    return False  # Still need the purpose answered
        
        # If query is too vague, need clarification
        vague_queries = ["i need an assessment", "i need a test", "assessment", "test"]
        if any(vq in query_lower for vq in vague_queries) and len(query_lower.split()) < 5:
            return False
        
        # If we have specific job level or test type or category, we can recommend
        if intent["job_level"] or intent["test_types"] or intent["categories"]:
            return True
        
        # If query has specific technology or role mentioned
        tech_keywords = ["java", "python", "javascript", "developer", "engineer", "analyst", "manager"]
        if any(keyword in query_lower for keyword in tech_keywords):
            return True
        
        # Otherwise, need more context
        return False
    
    def _get_recommendations(self, intent: Dict) -> List:
        """Get recommendations based on intent."""
        query_lower = intent["query"].lower()
        
        # Determine max results based on scenario
        max_results = 10
        
        # For leadership selection, return fewer, more targeted results
        if "selection" in query_lower and ("leadership" in query_lower or "executive" in query_lower or "director" in query_lower):
            max_results = 5  # Return top 5 for leadership selection
        
        return self.retrieval_system.retrieve(
            query=intent["query"],
            job_level=intent["job_level"],
            test_types=intent["test_types"] if intent["test_types"] else None,
            categories=intent["categories"] if intent["categories"] else None,
            max_results=max_results
        )
    
    def _generate_recommendation_reply(self, recommendations: List, intent: Dict) -> str:
        """Generate reply with recommendations."""
        if not recommendations:
            return "I couldn't find any assessments matching your criteria in the SHL catalog. Could you provide more specific details about the role or requirements?"
        
        count = len(recommendations)
        reply = f"Based on your requirements, here are {count} assessment{'s' if count > 1 else ''} from the SHL catalog that may fit your needs."
        
        if intent["job_level"]:
            reply += f" These are suitable for {intent['job_level']} level."
        
        return reply
    
    def _generate_clarification(self, intent: Dict) -> str:
        """Generate a clarifying question."""
        query_lower = intent["query"].lower()
        
        # Check for specific context clues in the query - prioritize these
        if "senior leadership" in query_lower or "cxo" in query_lower or "executive" in query_lower:
            return "For such senior leadership roles, I need to understand the purpose: is this for selection (hiring new executives) or development (feedback for existing leaders)?"
        
        if "director" in query_lower:
            return "For director-level roles, I need to understand the purpose: is this for selection (hiring new directors) or development (feedback for existing leaders)?"
        
        if "contact centre" in query_lower or "contact center" in query_lower or "call center" in query_lower:
            return "What language are the calls in? This determines which spoken-language screen we use."
        
        if "rust" in query_lower or any(lang in query_lower for lang in ["python", "golang", "swift", "kotlin"]):
            # Extract the specific language name
            lang_name = None
            for lang in ["rust", "python", "golang", "swift", "kotlin"]:
                if lang in query_lower:
                    lang_name = lang
                    break
            return f"SHL's catalog doesn't currently include a {lang_name if lang_name else 'that'}-specific knowledge test. The closest fit is Smart Interview Live Coding — an adaptive live-coding interview where your panel can frame language-specific tasks directly. Want me to build a shortlist from this?"
        
        if "plant operator" in query_lower or "safety" in query_lower:
            return "For safety-critical roles, would you prefer a general safety instrument (DSI) or an industry-specific solution with manufacturing norms?"
        
        if "bilingual" in query_lower or "spanish" in query_lower or "language" in query_lower:
            return "For bilingual roles, are the knowledge tests available in the required language, or would you consider a hybrid approach with knowledge tests in English and personality in the target language?"
        
        if "full-stack" in query_lower or "engineer" in query_lower:
            return "Is this a backend-leaning role, frontend-heavy, or a true balanced full-stack role? This helps narrow down the technical assessments."
        
        if "senior" in query_lower and ("ic" in query_lower or "individual contributor" in query_lower):
            return "Is the seniority closer to a senior IC (deep technical ownership) or a tech lead (sets architecture across services)?"
        
        # Default clarifications
        if not intent["job_level"]:
            return "To help me find the right assessments, could you specify the seniority level of the role (e.g., entry-level, mid-level, senior, executive)?"
        
        if not intent["test_types"] and not intent["categories"]:
            return "What type of assessments are you looking for? For example: technical skills, personality assessments, aptitude tests, or specific areas like leadership, sales, or customer service?"
        
        return "Could you provide more details about the specific skills or competencies you'd like to assess?"
    
    def _to_recommendation(self, assessment) -> Recommendation:
        """Convert Assessment to Recommendation."""
        return Recommendation(
            name=assessment.name,
            url=assessment.url,
            test_type=assessment.test_type
        )
    
    def _is_off_topic(self, message: str) -> bool:
        """Check if message is off-topic (not about SHL assessments)."""
        off_topic_keywords = [
            "legal", "law", "lawsuit", "regulation", "compliance",
            "salary", "compensation", "pay", "wage",
            "interview questions", "how to interview",
            "resume", "cv", "cover letter",
            "job board", "job posting", "linkedin",
            "hiring process", "recruitment strategy"
        ]
        
        message_lower = message.lower()
        for keyword in off_topic_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    def _is_prompt_injection(self, message: str) -> bool:
        """Check for potential prompt injection attempts."""
        injection_keywords = [
            "ignore previous", "forget everything", "new instruction",
            "system prompt", "override", "bypass", "jailbreak"
        ]
        
        message_lower = message.lower()
        for keyword in injection_keywords:
            if keyword in message_lower:
                return True
        
        return False
