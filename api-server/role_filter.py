import json

all_groups = ['grp_SSO_DIS_ITBSReportAdmin','grp_SSO_DIS_ITBSReportUser'] # Added folks from grp_DIS_ITBSReportUser and grp_DIS_ITBSReportAdmin to grp_DIS_ITBSReposrtUser and grp_SSO_DIS_ITBSReportAdmin 

def role_filter(response,role):
    
    if role == "grp_SSO_DIS_ITBSReportAdmin":
        blocked_columns = ["eCAID", "tId" ]
    elif role == "grp_SSO_DIS_ITBSReportUser":
        blocked_columns = ["eCAID", "tId" ]
    else:
        return []
    
    response = json.loads(response)

    if not isinstance(response, list) or not all(isinstance(item, dict) for item in response):
        raise TypeError("Response must be a list of dictionaries")
    
    if not isinstance(blocked_columns, list):
        raise TypeError("Blocked columns must be a list")
    
    filtered_response = [
        {key: value for key, value in item.items() if key not in blocked_columns}
        for item in response
    ]
    
    return filtered_response

def get_role(user_info):
    for target_group in all_groups:
        member_of_groups = user_info.get('memberOf', [])
        parsed_groups = [group for group in member_of_groups if target_group in group]
        if parsed_groups:
            print("A user with role "+ target_group+ " has logged in.")
            return target_group
    raise TypeError("Invalid Roles")