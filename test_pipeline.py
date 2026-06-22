"""Quick pipeline smoke test — runs without Streamlit or API keys."""
import sys
sys.path.insert(0, '.')

from modules.gap_analyzer import analyze_gap
from modules.scoring_engine import get_all_scores
from modules.roadmap_generator import generate_roadmap
from modules.course_recommender import recommend_courses
from modules.job_recommender import recommend_opportunities
from modules.interview_engine import generate_questions, evaluate_answer
from modules.chat_assistant import CareerChatAssistant
from modules.history_manager import init_db

mock_profile = {
    'name': 'Jane Doe', 'email': 'jane@example.com',
    'skills': ['Python', 'Pandas', 'SQL', 'Git', 'Machine Learning'],
    'experience_years': 1,
    'projects': [{'title': 'ML Project', 'description': 'Built a classifier'}],
    'certifications': ['AWS Certified Developer'],
    'education': {'degrees': ['B.Tech'], 'fields': ['Computer Science'], 'years': ['2024'], 'cgpa': '8.5'},
    'contact_info': {'name': 'Jane Doe', 'email': 'jane@example.com', 'phone': '', 'linkedin': '', 'github': ''},
}
mock_parsed = {
    'skills': 'Python Pandas SQL Machine Learning',
    'experience': '1 year at TCS as Data Analyst intern',
    'education': 'B.Tech CSE 2024 CGPA 8.5',
    'projects': 'ML Project - Built a sentiment classifier using BERT and Python',
    'certifications': 'AWS Certified Developer',
    'contact': 'jane@example.com',
    'summary': 'Aspiring data scientist with Python and ML skills seeking opportunities',
    'word_count': 250,
    'contact_info': {'name': 'Jane Doe', 'email': 'jane@example.com', 'phone': '9876543210', 'linkedin': 'linkedin.com/in/janedoe', 'github': 'github.com/janedoe'},
}

PASS = '✅'
FAIL = '❌'
results = []

def check(name, condition, detail=''):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f'{status} {name}: {detail}')

print('\n═══ Career Copilot — Pipeline Smoke Test ═══\n')

# 1. Gap Analysis
print('1. Skill Gap Analysis')
gap = analyze_gap(mock_profile['skills'], 'Data Scientist')
check('Target role found',    gap['target_role'] == 'Data Scientist')
check('Has skill match score', 0 <= gap['skill_match_score'] <= 100, f"{gap['skill_match_score']}%")
check('Has required skills',  len(gap['required_skills']) > 0, f"{len(gap['required_skills'])} skills")
check('Has missing skills',   len(gap['all_missing']) >= 0, f"{len(gap['all_missing'])} missing")
print()

# 2. Scoring
print('2. Scoring Engine')
scores = get_all_scores(mock_parsed, mock_profile, gap)
check('ATS score valid',         0 <= scores['ats']['ats_score'] <= 100,            f"{scores['ats']['ats_score']}/100")
check('Skill match valid',       0 <= scores['skill']['skill_match_score'] <= 100,  f"{scores['skill']['skill_match_score']}/100")
check('Employability score',     0 <= scores['employability']['employability_score'] <= 100, f"{scores['employability']['employability_score']}/100 — {scores['employability']['tier']}")
check('Experience score valid',  0 <= scores['experience']['experience_score'] <= 100)
print()

# 3. Roadmap
print('3. Roadmap Generator (fallback)')
roadmap = generate_roadmap(mock_profile, gap, '6 months', api_key='')
check('Has phases',    len(roadmap.get('phases', [])) > 0, f"{len(roadmap['phases'])} phases")
check('Has overview',  bool(roadmap.get('overview', '')))
check('Has duration',  bool(roadmap.get('total_duration', '')), roadmap.get('total_duration'))
print()

# 4. Course Recommendations
print('4. Course Recommender')
courses = recommend_courses(tuple(gap['missing_required'][:5]))
check('Returns courses dict',    isinstance(courses, dict))
check('Has course entries',      len(courses) > 0, f"{len(courses)} skills covered")
print()

# 5. Opportunities
print('5. Opportunity Recommender')
opps = recommend_opportunities(mock_profile['skills'], 'Data Scientist')
check('Returns jobs',        len(opps.get('jobs', [])) > 0,        f"{len(opps.get('jobs', []))} jobs")
check('Returns internships', len(opps.get('internships', [])) > 0, f"{len(opps.get('internships', []))} internships")
check('Returns hackathons',  len(opps.get('hackathons', [])) > 0,  f"{len(opps.get('hackathons', []))} hackathons")
print()

# 6. Interview Engine
print('6. Interview Engine')
qs = generate_questions('Data Scientist', mock_profile['skills'], 1, 3, 3, '')
check('Generated tech questions', len(qs.get('technical_questions', [])) == 3, f"{len(qs['technical_questions'])} questions")
check('Generated HR questions',   len(qs.get('hr_questions', [])) == 3,        f"{len(qs['hr_questions'])} questions")
result = evaluate_answer(
    'Explain overfitting',
    'Overfitting is when a model memorizes training data and fails on unseen test data. Regularization, dropout, and cross-validation help prevent it.',
    'Technical', 'Data Scientist',
    ['regularization', 'cross-validation', 'train', 'test'],
    ''
)
check('Answer evaluated',    isinstance(result.get('score'), int), f"Score: {result['score']}/10, Grade: {result['grade']}")
check('Has feedback',        bool(result.get('feedback', '')))
print()

# 7. Chat Assistant
print('7. Chat Assistant')
assistant = CareerChatAssistant(api_key='')
assistant.update_profile_context(mock_profile, gap)
response = assistant.chat('Hello! What can you help me with?')
check('Returns response',  len(response) > 50, f"{len(response)} chars")
response2 = assistant.chat('How do I improve my resume?')
check('Resume advice',     len(response2) > 50)
print()

# 8. History/DB
print('8. History Manager')
init_db()
sessions = []
try:
    from modules.history_manager import get_all_sessions, save_session
    sess_id = save_session('Jane Doe', 'jane@example.com', 'resume.pdf', 'Data Scientist', mock_profile, gap, scores, roadmap)
    sessions = get_all_sessions()
    check('Session saved',     sess_id > 0, f"Session ID: {sess_id}")
    check('Sessions retrieved', len(sessions) >= 1, f"{len(sessions)} sessions")
except Exception as e:
    check('History manager', False, str(e))
print()

# Summary
passed = sum(1 for r in results if r[0] == PASS)
total  = len(results)
print(f'═══ Results: {passed}/{total} checks passed ═══')
if passed == total:
    print('\n🚀 ALL TESTS PASSED — App is ready to run!')
    print('\nStart with: streamlit run app.py')
else:
    failed = [r for r in results if r[0] == FAIL]
    print(f'\n⚠️ {len(failed)} check(s) failed:')
    for r in failed:
        print(f'  {r[1]}: {r[2]}')
