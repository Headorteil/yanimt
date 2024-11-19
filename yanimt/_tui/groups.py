from typing import Any

from textual.widgets import Tree

from yanimt._database.models import Group, User


class GroupTree(Tree[str]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__("", *args, **kwargs)
        self.database = self.app.database  # pyright: ignore [reportAttributeAccessIssue]
        self.groups = None
        self.users = None

    def on_mount(self) -> None:
        self.root.expand()
        self.render_group()

    def render_group(self) -> None:
        self.clear()
        self.groups = list(self.database.get_groups())
        self.users = list(self.database.get_users())
        for group in self.groups:
            len_members = len(group.members) if group.members is not None else 0
            label = f"{group.sam_account_name} ({len_members})"
            self.root.add(label, data=group)

    def on_tree_node_expanded(self, message: Tree.NodeExpanded[Group | User]) -> None:
        if message.node.data is None or message.node.data.members is None:
            return

        needed_childs = len(message.node.data.members)
        if len(message.node.children) == needed_childs:
            return

        childs = 0
        to_add_members = set(message.node.data.members)
        for group in self.groups:  # pyright: ignore [reportOptionalIterable]
            if group.distinguished_name in to_add_members:
                len_members = len(group.members) if group.members is not None else 0
                label = f"{group.sam_account_name} ({len_members})"
                message.node.add(label, data=group)
                to_add_members.remove(group.distinguished_name)
                childs += 1

            if childs == needed_childs:
                break
        else:
            for user in self.users:  # pyright: ignore [reportOptionalIterable]
                if user.distinguished_name in message.node.data.members:
                    message.node.add(
                        user.sam_account_name, data=user, allow_expand=False
                    )
                    to_add_members.remove(user.distinguished_name)
                    childs += 1

                if childs == needed_childs:
                    break
            else:
                for member in to_add_members:
                    message.node.add(member, allow_expand=False)
