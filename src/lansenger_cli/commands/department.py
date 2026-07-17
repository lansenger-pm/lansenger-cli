import typer

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Query department information")


@app.command("detail")
def fetch_department_detail(
    department_id: str = typer.Argument(help="Department ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    tag_id: str = typer.Option("", "--tag-id", help="Tag ID"),
):
    """Fetch department detail information"""
    client = get_client()
    result = client.fetch_department_detail(
        department_id=department_id, user_token=user_token, tag_id=tag_id,
    )
    output_result(result, fields=[
        "id", "name", "parent_id", "has_children",
        "normal_members", "inactive_members",
    ], title="Department Detail")


@app.command("children")
def fetch_department_children(
    department_id: str = typer.Argument(help="Department ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch child departments"""
    client = get_client()
    result = client.fetch_department_children(department_id=department_id, user_token=user_token)
    if result.success and result.departments:
        output_list(result.departments, columns=["ID", "Name", "Parent ID", "Has Children"], row_mapper=lambda d: [
            d.get("id", ""), d.get("name", ""),
            (d.get("ancestorDepartments") or [{}])[0].get("id", ""), d.get("hasChildren", ""),
        ])
    else:
        output_result(result, title="Department Children")


@app.command("staffs")
def fetch_department_staffs(
    department_id: str = typer.Argument(help="Department ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(100, "--size", "-s", help="Page size"),
):
    """Fetch staff members in a department"""
    client = get_client()
    result = client.fetch_department_staffs(
        department_id=department_id, user_token=user_token,
        page=page, page_size=page_size,
    )
    if result.success and result.staffs:
        output_result(result, fields=["has_more", "total"], title="Department Staffs")
        output_list(result.staffs, columns=["Staff ID", "Name", "Org Name"], row_mapper=lambda s: [
            s.get("id", ""), s.get("name", ""),
            s.get("orgName", ""),
        ])
    else:
        output_result(result)
