import graphql
import config
from logger import logger
from datetime import datetime, timedelta

def prepare_release_comment(issue: dict, assignees: dict, release):
    """
    Prepare the comment from the given arguments and return it
    """

    comment = ''
    if assignees:
        for assignee in assignees:
            comment += f'@{assignee["login"]} '
    else:
        logger.info(f'No assignees found for issue #{issue["number"]}')

    comment += f'The Release is updated to: {release}.'
    logger.info(f'Issue {issue["title"]} | {comment}')

    return comment


def check_comment_exists(issue_id, expected_comment):
    """Check if the comment already exists on the issue."""
    comments = graphql.get_issue_comments(issue_id)
    for comment in comments:
        if expected_comment in comment.get('body', ''):
            return True
    return False
