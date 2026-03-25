"""
PRAL Agent System: Perceive, Act, Reason, Learn
"""

from datetime import datetime
from typing import List, Dict, Any
import asyncio
import json
import random

class PerceiveAgent:
    """
    Perceive Agent: Analyzes user input and train data
    - Understands search criteria
    - Analyzes user preferences
    - Scans train availability
    - Processes route information
    """
    
    def __init__(self):
        self.name = "Perceive Agent"
        self.status = "Active"
        self.activity_log = []
    
    async def perceive_search(self, search_params: Dict) -> Dict:
        """Analyze search parameters and train data"""
        perception = {
            'timestamp': datetime.now().isoformat(),
            'from': search_params.get('from'),
            'to': search_params.get('to'),
            'date': search_params.get('date'),
            'preferences': {
                'class_preference': search_params.get('class', 'AC3'),
                'time_preference': search_params.get('time'),
                'budget': search_params.get('budget'),
                'berth_preference': search_params.get('berth_preference', 'LOWER')
            },
            'perceived_data': {
                'route_distance': self._estimate_distance(search_params.get('from'), search_params.get('to')),
                'available_trains_estimate': 15,  # Mock estimate
                'peak_hours': ['18:00-22:00', '08:00-10:00'],
                'best_time_to_travel': self._best_travel_time(search_params.get('from'), search_params.get('to')),
                'user_type': self._identify_user_type(search_params),
                'demand_level': random.choice(['Low', 'Medium', 'High']),
            },
            'analysis_status': 'COMPLETED'
        }
        
        self.activity_log.append({
            'action': 'perceive_search',
            'result': perception,
            'timestamp': datetime.now().isoformat()
        })
        
        return perception
    
    def _estimate_distance(self, from_city: str, to_city: str) -> str:
        """Estimate distance between cities"""
        # Mock distances
        distance = {
            ('Delhi', 'Mumbai'): '1400 km',
            ('Mumbai', 'Bangalore'): '1300 km',
            ('Delhi', 'Kolkata'): '1500 km',
            ('Bangalore', 'Chennai'): '350 km',
        }
        key = (from_city, to_city) if (from_city, to_city) in distance else (to_city, from_city)
        return distance.get(key, '~800 km')
    
    def _best_travel_time(self, from_city: str, to_city: str) -> str:
        """Suggest best travel time"""
        return "Evening (18:00-22:00) for better fares"
    
    def _identify_user_type(self, search_params: Dict) -> str:
        """Identify user type"""
        if search_params.get('tatkal'):
            return 'Tatkal Buyer'
        elif search_params.get('budget') and search_params['budget'] < 500:
            return 'Budget Conscious'
        return 'Regular Traveler'
    
    def get_log(self):
        return self.activity_log


class ActAgent:
    """
    Act Agent: Executes booking and payment actions
    - Selects trains
    - Processes payments
    - Books seats
    - Generates confirmations
    """
    
    def __init__(self):
        self.name = "Act Agent"
        self.status = "Standby"
        self.activity_log = []
    
    async def execute_booking(self, booking_request: Dict) -> Dict:
        """Execute booking action"""
        booking_result = {
            'timestamp': datetime.now().isoformat(),
            'status': 'PROCESSING',
            'steps': [
                {
                    'step': 1,
                    'name': 'Validate Passengers',
                    'status': 'COMPLETED',
                    'duration': '2 seconds'
                },
                {
                    'step': 2,
                    'name': 'Check Availability',
                    'status': 'COMPLETED',
                    'duration': '1 second'
                },
                {
                    'step': 3,
                    'name': 'Select Seats',
                    'status': 'IN_PROGRESS',
                    'duration': '...'
                },
                {
                    'step': 4,
                    'name': 'Validate Payment',
                    'status': 'PENDING',
                    'duration': '...'
                },
                {
                    'step': 5,
                    'name': 'Generate PNR',
                    'status': 'PENDING',
                    'duration': '...'
                },
                {
                    'step': 6,
                    'name': 'Confirm Booking',
                    'status': 'PENDING',
                    'duration': '...'
                }
            ],
            'selected_train': booking_request.get('train_id'),
            'selected_class': booking_request.get('class'),
            'passengers': booking_request.get('passengers_count'),
            'total_amount': booking_request.get('amount'),
            'pnr': None,  # Will be generated after payment
        }
        
        # Simulate booking execution
        await asyncio.sleep(0.1)
        
        # Generate PNR
        pnr = f"AB{datetime.now().strftime('%y%m%d')}{booking_request.get('train_id', '0000')[-4:]}"
        booking_result['pnr'] = pnr
        booking_result['status'] = 'CONFIRMED'
        booking_result['steps'][2]['status'] = 'COMPLETED'
        booking_result['steps'][2]['duration'] = '2 seconds'
        
        self.activity_log.append({
            'action': 'execute_booking',
            'booking_id': pnr,
            'result': booking_result,
            'timestamp': datetime.now().isoformat()
        })
        
        return booking_result
    
    async def execute_tatkal_booking(self, tatkal_request: Dict) -> Dict:
        """Execute Tatkal booking at scheduled time"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'booking_type': 'Tatkal',
            'scheduled_time': tatkal_request.get('scheduled_time'),
            'status': 'SCHEDULED',
            'action': 'Will execute booking at scheduled time'
        }
        
        self.activity_log.append({
            'action': 'schedule_tatkal',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def get_log(self):
        return self.activity_log


class ReasonAgent:
    """
    Reason Agent: Makes intelligent decisions
    - Evaluates train options
    - Ranks trains
    - Provides recommendations
    - Explains decisions
    """
    
    def __init__(self):
        self.name = "Reason Agent"
        self.status = "Processing"
        self.activity_log = []
    
    async def reason_train_selection(self, trains: List[Dict], user_preferences: Dict) -> Dict:
        """Reason about best train selection"""
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'trains_evaluated': len(trains),
            'ranking_factors': {
                'availability': 0.25,
                'price': 0.25,
                'duration': 0.20,
                'tatkal_probability': 0.20,
                'comfort': 0.10
            },
            'top_recommendations': [],
            'reasoning': "Evaluated trains based on user preferences and availability"
        }
        
        # Mock rankings
        for i, train in enumerate(trains[:3]):
            score = 100 - (i * 15)
            reasoning['top_recommendations'].append({
                'rank': i + 1,
                'train_id': train.get('_id'),
                'train_name': train.get('name'),
                'score': score,
                'why_selected': self._generate_reasoning(train, user_preferences)
            })
        
        self.activity_log.append({
            'action': 'reason_selection',
            'result': reasoning,
            'timestamp': datetime.now().isoformat()
        })
        
        return reasoning
    
    def _generate_reasoning(self, train: Dict, preferences: Dict) -> str:
        """Generate reasoning for train selection"""
        reasons = []
        
        if train['availability']['confirmed'] > 50:
            reasons.append("High availability")
        if 'price' in train:
            reasons.append("Competitive pricing")
        if train.get('rating', 0) > 4.5:
            reasons.append("Highly rated")
        
        return " + ".join(reasons) if reasons else "Meets your criteria"
    
    def get_log(self):
        return self.activity_log


class LearnAgent:
    """
    Learn Agent: Learns from user behavior
    - Stores booking patterns
    - Optimizes preferences
    - Improves recommendations
    - Analyzes success/failure
    """
    
    def __init__(self):
        self.name = "Learn Agent"
        self.status = "Learning"
        self.learned_patterns = {
            'user_preferences': {},
            'successful_bookings': 0,
            'failed_bookings': 0,
            'booking_patterns': {},
            'accuracy_improvement': 0.0
        }
        self.activity_log = []
    
    async def learn_from_booking(self, booking_data: Dict, success: bool) -> Dict:
        """Learn from booking outcome"""
        learning_result = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'learned_insights': {
                'user_prefers': self._extract_preferences(booking_data),
                'success_factors': self._identify_success_factors(booking_data) if success else [],
                'improvement_areas': self._identify_improvements(booking_data),
                'confidence_score': 0.85 if success else 0.45
            },
            'pattern_updated': True,
            'recommendation_accuracy': '87.5%'
        }
        
        # Update learning patterns
        if success:
            self.learned_patterns['successful_bookings'] += 1
        else:
            self.learned_patterns['failed_bookings'] += 1
        
        self.activity_log.append({
            'action': 'learn_booking',
            'result': learning_result,
            'timestamp': datetime.now().isoformat()
        })
        
        return learning_result
    
    def _extract_preferences(self, booking_data: Dict) -> Dict:
        """Extract learned preferences"""
        return {
            'preferred_class': booking_data.get('class'),
            'preferred_time': booking_data.get('departure_time'),
            'budget_range': f"₹{booking_data.get('amount', 0)}"
        }
    
    def _identify_success_factors(self, booking_data: Dict) -> List[str]:
        """Identify what made booking successful"""
        return [
            "High seat availability",
            "Competitive pricing",
            "User chose recommended train"
        ]
    
    def _identify_improvements(self, booking_data: Dict) -> List[str]:
        """Identify areas for improvement"""
        return [
            "Could suggest more regional trains",
            "Better time slot recommendations"
        ]
    
    def get_log(self):
        return self.activity_log
    
    def get_learned_patterns(self):
        return self.learned_patterns


class PRALOrchestrator:
    """
    PRAL Orchestrator: Coordinates all 4 agents
    """
    
    def __init__(self):
        self.perceive_agent = PerceiveAgent()
        self.act_agent = ActAgent()
        self.reason_agent = ReasonAgent()
        self.learn_agent = LearnAgent()
        self.orchestration_log = []
    
    async def orchestrate_search_and_book(self, search_params: Dict, trains: List[Dict]) -> Dict:
        """Orchestrate complete search to booking flow"""
        
        # Phase 1: PERCEIVE - Understand user needs
        print("🔍 PERCEIVE: Analyzing search criteria...")
        perception = await self.perceive_agent.perceive_search(search_params)
        
        # Phase 2: REASON - Evaluate options
        print("🧠 REASON: Evaluating train options...")
        reasoning = await self.reason_agent.reason_train_selection(trains, search_params)
        
        # Phase 3: ACT - Execute boking (if user selects)
        print("⚡ ACT: Ready to execute booking...")
        
        # Phase 4: LEARN - Record for future improvements
        print("📚 LEARN: Recording patterns for future...")
        
        result = {
            'orchestration_id': f"orch_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'phases': {
                'perceive': perception,
                'reason': reasoning,
                'act': 'Awaiting user selection',
                'learn': 'Will record outcome'
            },
            'recommended_trains': reasoning.get('top_recommendations'),
            'status': 'AWAITING_USER_SELECTION'
        }
        
        self.orchestration_log.append(result)
        return result
    
    def get_all_logs(self):
        """Get logs from all agents"""
        return {
            'perceive': self.perceive_agent.get_log(),
            'act': self.act_agent.get_log(),
            'reason': self.reason_agent.get_log(),
            'learn': self.learn_agent.get_log(),
            'orchestration': self.orchestration_log
        }

# Example usage
import random

if __name__ == "__main__":
    print("🤖 PRAL Agent System Initialized\n")
    
    # Create orchestrator
    orchestrator = PRALOrchestrator()
    
    # Mock data
    search_params = {
        'from': 'Delhi',
        'to': 'Mumbai',
        'date': '2024-03-25',
        'class': 'AC3',
        'time': '18:00',
        'budget': 2000,
        'berth_preference': 'LOWER'
    }
    
    mock_trains = [
        {
            '_id': f'train_000{i}',
            'name': f'Express {i}',
            'from': 'Delhi',
            'to': 'Mumbai',
            'availability': {'confirmed': random.randint(10, 150)},
            'rating': round(random.uniform(3.5, 4.9), 1)
        }
        for i in range(1, 6)
    ]
    
    print("Orchestrating search and booking flow...")
    # asyncio.run(orchestrator.orchestrate_search_and_book(search_params, mock_trains))
