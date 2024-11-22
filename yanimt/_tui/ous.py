from typing import Any

from textual.widgets import Tree

from yanimt._database.models import Group, User


class OrganisationalUnitsTree(Tree[str]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__("", *args, **kwargs)
        self.database = self.app.database  # pyright: ignore [reportAttributeAccessIssue]
        self.groups = None
        self.users = None
        self.computers = None

    def on_mount(self) -> None:
        self.root.expand()
        self.render_organisational_units()

    def render_organisational_units(self) -> None:
        self.clear()
        self.ous = list(self.database.get_organisational_units())
        self.groups = list(self.database.get_groups())
        self.users = list(self.database.get_users())
        self.computers = list(self.database.get_computers())
        for ou in self.ous:
            len_members = len(ou.members) if ou.members is not None else 0
            label = f"{ou.name} ({len_members})"
            expand = True
            if len_members == 0:
                expand = False
            self.root.add(label, data=ou, allow_expand=expand)

    def on_tree_node_expanded(self, message: Tree.NodeExpanded[Group | User]) -> None:
        if message.node.data is None or message.node.data.members is None:
            return

        needed_childs = len(message.node.data.members)
        if len(message.node.children) == needed_childs:
            return

        childs = 0
        to_add_members = set(message.node.data.members)
        for ou in self.ous:  # pyright: ignore [reportOptionalIterable]
            if ou.distinguished_name in message.node.data.members:
                len_members = len(ou.members) if ou.members is not None else 0
                label = f"{ou.name} ({len_members})"
                expand = True
                if len_members == 0:
                    expand = False
                message.node.add(label, data=ou, allow_expand=expand)
                to_add_members.remove(ou.distinguished_name)
                childs += 1

            if childs == needed_childs:
                return
        for group in self.groups:  # pyright: ignore [reportOptionalIterable]
            if group.distinguished_name in to_add_members:
                message.node.add(group.sam_account_name, data=group, allow_expand=False)
                to_add_members.remove(group.distinguished_name)
                childs += 1

            if childs == needed_childs:
                return
        for computer in self.computers:  # pyright: ignore [reportOptionalIterable]
            if computer.user.distinguished_name in to_add_members:
                message.node.add(computer.rich(), data=computer, allow_expand=False)
                to_add_members.remove(computer.user.distinguished_name)
                childs += 1

            if childs == needed_childs:
                return
        for user in self.users:  # pyright: ignore [reportOptionalIterable]
            if user.distinguished_name in message.node.data.members:
                message.node.add(user.rich(), data=user, allow_expand=False)
                to_add_members.remove(user.distinguished_name)
                childs += 1

            if childs == needed_childs:
                return
        for member in to_add_members:
            message.node.add(member, allow_expand=False)
