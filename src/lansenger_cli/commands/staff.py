import typer
from typing import Optional, List

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Query staff/contacts information")


@app.command("basic-info")
def fetch_staff_basic_info(
    staff_id: str = typer.Argument(help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_staff_basic_info(staff_id=staff_id, user_token=user_token)
    output_result(result, fields=[
        "org_id", "org_name", "name", "gender", "signature",
        "avatar_url", "status", "departments",
    ], title="Staff Basic Info")


@app.command("detail")
def fetch_staff_detail(
    staff_id: str = typer.Argument(help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_staff_detail(staff_id=staff_id, user_token=user_token)
    output_result(result, fields=[
        "org_id", "org_name", "name", "gender", "email",
        "mobile_phone", "avatar_url", "career", "tags",
    ], title="Staff Detail")


@app.command("ancestors")
def fetch_department_ancestors(
    staff_id: str = typer.Argument(help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_department_ancestors(staff_id=staff_id, user_token=user_token)
    if result.success and result.ancestor_groups:
        output_list(result.ancestor_groups, columns=["Department Group"], row_mapper=lambda g: [str(g)])
    else:
        output_result(result, title="Department Ancestors")


@app.command("id-mapping")
def fetch_staff_id_mapping(
    org_id: str = typer.Argument(help="Organization ID"),
    id_type: str = typer.Argument(help="ID type: employ_id, mobile, mail, login, external_id"),
    id_value: str = typer.Argument(help="ID value to map"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_staff_id_mapping(
        org_id=org_id, id_type=id_type, id_value=id_value, user_token=user_token,
    )
    output_result(result, fields=["staff_id"], title="Staff ID Mapping")


@app.command("org-extra-fields")
def fetch_org_extra_field_ids(
    org_id: str = typer.Argument(help="Organization ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(1000, "--size", "-s", help="Page size"),
):
    client = get_client()
    result = client.fetch_org_extra_field_ids(
        org_id=org_id, user_token=user_token, page=page, page_size=page_size,
    )
    output_result(result, fields=["has_more", "total"], title="Org Extra Fields")


@app.command("search")
def search_staff(
    keyword: str = typer.Argument(help="Search keyword"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID context"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Recursive search"),
    sector_ids: Optional[List[str]] = typer.Option(None, "--sector", help="Sector IDs"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Page number"),
    page_size: Optional[int] = typer.Option(None, "--size", "-s", help="Page size"),
):
    client = get_client()
    result = client.search_staff(
        keyword=keyword, user_token=user_token, user_id=user_id,
        recursive=recursive, sector_ids=sector_ids,
        page=page, page_size=page_size,
    )
    output_result(result, fields=["has_more", "total"], title="Staff Search")


@app.command("org-info")
def fetch_org_info(
    org_id: str = typer.Argument(help="Organization ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_org_info(org_id=org_id, user_token=user_token)
    output_result(result, fields=["org_id", "org_name", "icon_url"], title="Org Info")