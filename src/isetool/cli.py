#!/usr/bin/env /usr/bin/python3

import click
import json
from isetool.ise import ISE
import os
import pprint

pp = pprint.PrettyPrinter(indent=4)


class Default(dict):
    def __missing__(self, key):
        return key


filterOperatorChoices = ["EQ", "NEQ", "GT", "LT", "STARTSW", "NSTARTSW", "ENDSW", "NENDSW", "CONTAINS", "NCONTAINS"]
filterOperatorChoices_help = "EQ: Equals, NEQ: Not Equals, GT: Greater Than, LT: Less Then, STARTSW: Starts With,"
"NSTARTSW: Not Starts With, ENDSW: Ends With, NENDSW: Not Ends With, CONTAINS: Contains, NCONTAINS: Not Contains"

# Filter fields allowed in all user operations
#
filterFieldUserChoices = ["lastName", "identityGroup", "name", "description", "email", "enabled"]


@click.group()
@click.option(
    "--config",
    metavar="CONFIG_FILE",
    help="Configuaration file to load.",
    default=os.environ["HOME"] + "/.config/isetool/config.json",
    envvar='ISETOOL_CONFIG_FILE',
    type=click.File(mode='r')
)
@click.pass_context
def cli(ctx, config):
    """Entry Point for command."""
    ctx.obj = {}
    ctx.obj['config'] = config
    pass


@cli.command()
@click.option(
    "--filter-field",
    type=click.Choice(filterFieldUserChoices, case_sensitive=False),
    default="name",
    help="Field to use in the filter match"
)
@click.option(
    "--filter-operator",
    type=click.Choice(filterOperatorChoices, case_sensitive=False),
    default="EQ",
    help=filterOperatorChoices_help
)
@click.option("--filter-match", help="Filter match string.", metavar="MATCH")
@click.pass_obj
def userlist(ctx, filter_field, filter_operator, filter_match):
    """List users on the ISE deployment."""

    cfg = json.load(obj['config'])

    if filter_match:
        filter = filter_field + "." + filter_operator + "." + filter_match
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


@cli.command()
@click.option(
    "--filter-field",
    type=click.Choice(["name", "description"], case_sensitive=False),
    default="name",
    help="Field to use in the filter match"
)
@click.option(
    "--filter-operator",
    type=click.Choice(filterOperatorChoices, case_sensitive=False),
    default="EQ",
    help=filterOperatorChoices_help
)
@click.option("--filter-match", help="Filter match string.", metavar="MATCH")
@click.pass_obj
def grouplist(obj, filter_field, filter_operator, filter_match):
    """List identity groups on the ISE deployment."""

    pp.pprint(obj)

    cfg = json.load(obj['config'])

    pp.pprint(cfg)
    if filter_match:
        filter = filter_field + "." + filter_operator + "." + filter_match

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


@cli.command()
@click.option(
    "-g", "--group", metavar="GROUPID", required=True, help="Group ID of the group the user(s) should be added to."
)
@click.option(
    "--filter-field",
    type=click.Choice(filterFieldUserChoices, case_sensitive=False),
    default="name",
    help="Field to use in the filter match."
)
@click.option(
    "--filter-operator",
    type=click.Choice(filterOperatorChoices, case_sensitive=False),
    default="EQ",
    help=filterOperatorChoices_help
)
@click.option("--filter-match", help="Filter match string.", metavar="MATCH")
@click.pass_obj
def useraddgroup(obj, group, filter_field, filter_operator, filter_match):
    """Add user(s) to an identity group."""

    cfg = json.load(obj['config'])
    if filter_match:
        filter = filter_field + "." + filter_operator + "." + filter_match
        print("Updating users with filter: " + filter)
    else:
        filter = None
        print("Updating all users.")

    newGroup = group

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
