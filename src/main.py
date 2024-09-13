from logger import logger
import config
import utils
import graphql

def notify_release_changes():
    if config.is_enterprise:
        issues = graphql.get_project_issues(
            owner=config.repository_owner,
            owner_type=config.repository_owner_type,
            project_number=config.project_number,
            release_field_name=config.release_field_name,
            filters={'open_only': True}
        )
    else:
        # Get the issues
        issues = graphql.get_repo_issues(
            owner=config.repository_owner,
            repository=config.repository_name,
            release_field_name=config.release_field_name
        )

    # Check if there are issues available
    if not issues:
        logger.info('No issues have been found')
        return

    for projectItem in issues:
        # Safely extract 'content' from projectItem
        issue = projectItem.get('content')
        if not issue:
            logger.error(f"Missing 'content' in project item: {projectItem}")
            continue

        # Get the list of assignees
        assignees = issue.get('assignees', {}).get('nodes', [])
        
        # Get the release value
        release = None
        try:
            release = projectItem.get('fieldValueByName', {}).get('name')
        except (AttributeError, ValueError) as e:
            continue  # Skip this issue and move to the next

        issue_title = issue.get('title', 'Unknown Title')
        issue_id = issue.get('id', 'Unknown ID')

        if not release:
            logger.info(f'No release found for issue {issue_title}')
            continue
        
        expected_comment = f"The Release is updated to: {release}."
      
        # Check if the comment already exists
        if not utils.check_comment_exists(issue_id, expected_comment):
            if config.notification_type == 'comment':
                # Prepare the notification content
                comment = utils.prepare_release_comment(
                    issue=issue,
                    assignees=assignees, 
                    release=release
                )
                
                if not config.dry_run:
                    try:
                        # Add the comment to the issue
                        graphql.add_issue_comment(issue_id, comment)
                        logger.info(f'Comment added to issue with title {issue_title}. Release is {release}.')
                    except Exception as e:
                        logger.error(f"Failed to add comment to issue {issue_title} (ID: {issue_id}): {e}")
                else:
                    logger.info(f'DRY RUN: Comment prepared for issue with title {issue_title}. Release is {release}.')

def main():
    logger.info('Process started...')
    if config.dry_run:
        logger.info('DRY RUN MODE ON!')

    notify_release_changes()

if __name__ == "__main__":
    main()
