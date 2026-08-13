import unittest

from widgets.git_status_panel import GitStatusPanel, RepoStatus


class GitStatusPanelTest(unittest.TestCase):
    def test_sort_prioritizes_conflicts_then_actionable_states(self):
        statuses = [
            RepoStatus("synced", upstream=True),
            RepoStatus("ahead", upstream=True, ahead=1),
            RepoStatus("behind", upstream=True, behind=1),
            RepoStatus("dirty", upstream=True, dirty=1),
            RepoStatus("conflict", upstream=True, conflict=True),
        ]
        self.assertEqual([status.name for status in sorted(statuses, key=RepoStatus.sort_key)], ["conflict", "dirty", "behind", "ahead", "synced"])

    def test_format_uses_three_levels_for_actionable_repo(self):
        text = GitStatusPanel._format_result(RepoStatus("repo", "main", dirty=2, behind=1, upstream=True))
        self.assertEqual(text.splitlines(), ["[yellow]*[/] [bold]repo[/]", "  main  [dim]behind 1[/]", "  [yellow]2 changed[/]"])


if __name__ == "__main__":
    unittest.main()
