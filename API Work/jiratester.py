from jira import JIRA

JIRA_SERVER = 'https://grantow.atlassian.net'
JIRA_USER = 'grantow@umich.edu'
JIRA_API_TOKEN 
# Establish the connection
jira = JIRA(
    options={'server': JIRA_SERVER},
    basic_auth=(JIRA_USER, JIRA_API_TOKEN)
)


# Project details
project_key = 'Spartahack 2026'
project_name = 'Spartahack 2026'
project_lead = 'grantow' # Use the Atlassian Account ID for Jira Cloud
project_type = 'software' # 'business' or 'service_desk' are other options

# Create the project
try:
    new_project = jira.create_project(
        project_key,
        project_name,
        project_lead,
        project_type
    )
    print(f"Project '{new_project.name}' created with key '{new_project.key}'")
except Exception as e:
    print(f"Failed to create project: {e}")

projects = jira.projects()

print(f'{projects}')

# new_issue = jira.create_issue(project='SCRUM', summary='New issue from jira-python',
#                               description='Look into this one', issuetype={'name': 'Bug'})