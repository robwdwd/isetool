#!/usr/bin/env /usr/bin/python3

import argparse
import json
from isetool.ise import ISE
import os
import pprint
import sys

pp = pprint.PrettyPrinter(indent=4)


class Default(dict):
    def __missing__(self, key):
        return key


def doUserList(args=None):

    print("Entering Function doUserList")

    if args.filter_match:
        filter = args.filter_field + "." + args.filter_operator + "." + args.filter_match
        print("Getting users with filter: " + filter)
    else:
        filter = None
        print("Getting all users.")

    # Open session to the ISE server.
    #
    iseSession = ISE(cfg["server"]["host"], cfg["server"]["port"], cfg["server"]["username"], cfg["server"]["password"])
    iseSession.connect()

    # Loop through the pages of results until no more pages
    #
    page = 1

    while True:
        result = iseSession.getUserList(page, filter)
        for user in result["resources"]:
            userRecord = iseSession.getUserByID(user["id"], True)

            if userRecord:
                print(
                    "{name},{firstName} {lastName},{email},{enabled},{idenityGroupNames}".format_map(
                        Default(userRecord)
                    )
                )

        if "nextPage" not in result:
            break
        else:
            page = page + 1

    iseSession.close()


def doGroupList(args=None):

    if args.filter_match:
        filter = args.filter_field + "." + args.filter_operator + "." + args.filter_match

        print("Getting idenity groups with filter: " + filter)
    else:
        filter = None
        print("Getting all identity groups.")

    # Open session to the ISE server.
    #
    iseSession = ISE(cfg["server"]["host"], cfg["server"]["port"], cfg["server"]["username"], cfg["server"]["password"])
    iseSession.connect()

    # Get the group list pages one at a time until no more pages
    #
    page = 1

    while True:
        result = iseSession.getGroupList(page, filter)
        for group in result["resources"]:
            groupRecord = iseSession.getGroupByID(group["id"])
            if groupRecord:
                print("{name},{id},{description}".format_map(Default(groupRecord)))

        if "nextPage" not in result:
            break
        else:
            page = page + 1

    iseSession.close()


def doUserAddGroup(args=None):
    if args.filter_match:
        filter = args.filter_field + "." + args.filter_operator + "." + args.filter_match
        print("Updating users with filter: " + filter)
    else:
        filter = None
        print("Updating all users.")

    newGroup = args.group

    # Open session to the ISE server.
    #
    iseSession = ISE(cfg["server"]["host"], cfg["server"]["port"], cfg["server"]["username"], cfg["server"]["password"])
    iseSession.connect()

    page = 1

    while True:
        result = iseSession.getUserList(page, filter)
        for user in result["resources"]:
            userRecord = iseSession.getUserByID(user["id"])

            if userRecord:
                del userRecord["password"]
                del userRecord["enablePassword"]
                del userRecord["link"]

                userRecord["identityGroups"] = userRecord["identityGroups"] + "," + newGroup
                sdkresponse = iseSession.updateUserByID(user["id"], userRecord)
                print("Adding new group to user: {}".format(userRecord["name"]))

        if "nextPage" not in result:
            break
        else:
            page = page + 1

    iseSession.close()

def main():
    with open(os.environ["HOME"] + "/.cfg/iseapi.json") as cfgfile:
        cfg = json.load(cfgfile)

    # Set up the filter operators as this is common with all API calls.
    #
    filterOperatorChoices = ["EQ", "NEQ", "GT", "LT", "STARTSW", "NSTARTSW", "ENDSW", "NENDSW", "CONTAINS", "NCONTAINS"]
    filterOperatorChoices_help = "EQ: Equals, NEQ: Not Equals, GT: Greater Than, LT: Less Then, STARTSW: Starts With,"
    "NSTARTSW: Not Starts With, ENDSW: Ends With, NENDSW: Not Ends With, CONTAINS: Contains, NCONTAINS: Not Contains"

    # Filter fields allowed in all user operations
    #
    filterFieldUserChoices = ["lastName", "identityGroup", "name", "description", "email", "enabled"]

    parser = argparse.ArgumentParser(description="Run API operations on a Cisco ISE deployment.")

    # Add sub commands with sub parser.
    #
    subparsers = parser.add_subparsers(help="Subcommand Help", title="subcommands", description="Valid Subcommands")

    parserUserList = subparsers.add_parser("userlist", help="userlist help")

    argUserListFilter = parserUserList.add_argument_group(
        title="Filtering", description="Filtering options to control which users are returned."
    )

    argUserListFilter.add_argument(
        "--filter-field", choices=filterFieldUserChoices, default="name", help="Field to use in the filter match"
    )

    argUserListFilter.add_argument(
        "--filter-operator", choices=filterOperatorChoices, default="EQ", help=filterOperatorChoices_help
    )

    argUserListFilter.add_argument("--filter-match", help="Filter match string.", metavar="MATCH")
    parserUserList.set_defaults(func=doUserList)

    # Add arguments to the UserAddGroup sub commands
    #
    parserUserAddGroup = subparsers.add_parser("useraddgroup", help="useraddgroup help")

    parserUserAddGroup.add_argument(
        "-g", "--group", metavar="GROUPID", required=True, help="Group ID of the group the user(s) should be added to."
    )

    argUserAddGroupFilter = parserUserAddGroup.add_argument_group(
        title="Filtering", description="Filtering options to control which users have the new group applied."
    )

    argUserAddGroupFilter.add_argument(
        "--filter-field", choices=filterFieldUserChoices, default="name", help="Field to use in the filter match"
    )

    argUserAddGroupFilter.add_argument(
        "--filter-operator", choices=filterOperatorChoices, default="EQ", help=filterOperatorChoices_help
    )

    argUserAddGroupFilter.add_argument("--filter-match", help="Filter match string.", metavar="MATCH")

    parserUserAddGroup.set_defaults(func=doUserAddGroup)

    # Add arguments to the grouplist sub command.
    #
    parserGroupList = subparsers.add_parser("grouplist", help="grouplist help")

    argGroupListFilter = parserGroupList.add_argument_group(
        title="Filtering", description="Filtering options to control which groups are listed."
    )

    argGroupListFilter.add_argument(
        "--filter-field", choices=["name", "description"], default="name", help="Field to use in the filter match"
    )

    argGroupListFilter.add_argument(
        "--filter-operator", choices=filterOperatorChoices, default="EQ", help=filterOperatorChoices_help
    )

    argGroupListFilter.add_argument("--filter-match", help="Filter match string.", metavar="MATCH")
    parserGroupList.set_defaults(func=doGroupList)

    # Parse the arguments and call the function for the sub-command.
    #
    prog_args = parser.parse_args()
    prog_args.func(prog_args)

if __name__ == "__main__":
    main()
