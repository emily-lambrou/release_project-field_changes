from pprint import pprint
import requests
import logging
import config
import utils
import json

def get_repo_issues(owner, repository, release_field_name, after=None, issues=None):
    query = """
    query GetRepoIssues($owner: String!, $repo: String!, $release: String!, $after: String) {
          repository(owner: $owner, name: $repo) {
            issues(first: 100, after: $after, states: [OPEN]) {
              nodes {
                id
                title
                number
                url
                assignees(first:100) {
                  nodes {
                    name
                    email
                    login
                  }
                }
                projectItems(first: 10) {
                  nodes {
                    project {
                      number
                      title
                    }
                    fieldValueByName(name: $release) {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        id
                        name
                      }
                    }
                  }
                }
              }
              pageInfo {
                endCursor
                hasNextPage
                hasPreviousPage
              }
              totalCount
            }
          }
        }
    """

    variables = {
        'owner': owner,
        'repo': repository,
        'release': release_field_name,
        'after': after
    }

    response = requests.post(
        config.api_endpoint,
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {config.gh_token}"}
    )

    if response.json().get('errors'):
        print(response.json().get('errors'))

    pageinfo = response.json().get('data').get('repository').get('issues').get('pageInfo')
    if issues is None:
        issues = []
    issues = issues + response.json().get('data').get('repository').get('issues').get('nodes')
    if pageinfo.get('hasNextPage'):
        return get_repo_issues(
            owner=owner,
            repository=repository,
            after=pageinfo.get('endCursor'),
            issues=issues,
            release_field_name=release_field_name
        )

    return issues


def get_project_issues(owner, owner_type, project_number, release_field_name, filters=None, after=None, issues=None):
    query = f"""
    query GetProjectIssues($owner: String!, $projectNumber: Int!, $release: String!, $after: String)  {{
          {owner_type}(login: $owner) {{
            projectV2(number: $projectNumber) {{
              id
              title
              number
              items(first: 100, after: $after) {{
                nodes {{
                  id
                  fieldValueByName(name: $release) {{
                    ... on ProjectV2ItemFieldSingleSelectValue {{
                      id
                      name
                    }}
                  }}
                  content {{
                    ... on Issue {{
                      id
                      title
                      number
                      state
                      url
                      assignees(first: 20) {{
                        nodes {{
                          name
                          email
                          login
                        }}
                      }}
                    }}
                  }}
                }}
                pageInfo {{
                  endCursor
                  hasNextPage
                  hasPreviousPage
                }}
                totalCount
              }}
            }}
          }}
        }}
    """

    variables = {
        'owner': owner,
        'projectNumber': project_number,
        'release': release_field_name,
        'after': after
    }

    response = requests.post(
        config.api_endpoint,
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {config.gh_token}"}
    )

    if response.json().get('errors'):
        logging.error(response.json().get('errors'))
        return []

    page_info = response.json().get('data').get(owner_type).get('projectV2').get('items').get('pageInfo')
    nodes = response.json().get('data').get(owner_type).get('projectV2').get('items').get('nodes')

    if filters:
        filtered_issues = []
        for node in nodes:
            if filters.get('open_only') and node['content'].get('state') != 'OPEN':
                continue
            filtered_issues.append(node)
        nodes = filtered_issues

    issues = issues or []
    issues += nodes

    if page_info.get('hasNextPage'):
        return get_project_issues(
            owner=owner,
            owner_type=owner_type,
            project_number=project_number,
            after=page_info.get('endCursor'),
            filters=filters,
            issues=issues,
            release_field_name=release_field_name
        )

    return issues

def add_issue_comment(issue_id, comment):
    mutation = """
    mutation AddIssueComment($issueId: ID!, $comment: String!) {
        addComment(input: {subjectId: $issueId, body: $comment}) {
            clientMutationId
        }
    }
    """

    variables = {
        'issueId': issue_id,
        'comment': comment
    }

    try:
        response = requests.post(
            config.api_endpoint,
            json={"query": mutation, "variables": variables},
            headers={"Authorization": f"Bearer {config.gh_token}"}
        )
        data = response.json()

        if 'errors' in data:
            logging.error(f"GraphQL mutation errors: {data['errors']}")

        return data.get('data')

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return {}

def get_issue_comments(issue_id):
    query = """
    query GetIssueComments($issueId: ID!, $afterCursor: String) {
        node(id: $issueId) {
            ... on Issue {
                comments(first: 100, after: $afterCursor) {
                    nodes {
                        body
                        createdAt
                        author {
                            login
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    }
    """

    variables = {
        'issueId': issue_id,
        'afterCursor': None
    }

    all_comments = []

    try:
        while True:
            response = requests.post(
                config.api_endpoint,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {config.gh_token}"}
            )

            data = response.json()

            if 'errors' in data:
                logging.error(f"GraphQL query errors: {data['errors']}")
                break

            comments_data = data.get('data', {}).get('node', {}).get('comments', {})
            comments = comments_data.get('nodes', [])
            all_comments.extend(comments)

            pageinfo = comments_data.get('pageInfo', {})
            if not pageinfo.get('hasNextPage'):
                break

            # Set the cursor for the next page
            variables['afterCursor'] = pageinfo.get('endCursor')

        return all_comments

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return []
