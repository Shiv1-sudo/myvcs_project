"""MyVCS command-line interface."""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from myvcs.common.application_config import (
    ApplicationConfig,
    load_configuration,
)
from myvcs.common.application_exceptions import (
    MyVCSError,
)
from myvcs.common.application_logging import (
    configure_logging,
    get_logger,
)
from myvcs.objects.blob_object import BlobObject
from myvcs.references.reference_manager import (
    ReferenceManager,
)
from myvcs.repository.object_store import ObjectStore
from myvcs.repository.repository_manager import (
    RepositoryManager,
)

from myvcs.services.add_service import AddService
from myvcs.services.commit_service import CommitService
from myvcs.services.status_service import StatusService
from myvcs.services.diff_service import DiffService
from myvcs.services.branch_service import BranchService
from myvcs.services.checkout_service import CheckoutService
from myvcs.services.merge_service import MergeService
from myvcs.services.tag_service import TagService
from myvcs.services.remote_service import RemoteService
from myvcs.services.clone_service import CloneService
from myvcs.services.garbage_collection_service import (
    GarbageCollectionService,
)

from myvcs.storage.pack_file import PackFile


LOGGER = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="myvcs",
        description=(
            "Git-like version control system "
            "implemented in Python."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # ---------------------------------------------------------
    # init
    # ---------------------------------------------------------

    subparsers.add_parser(
        "init",
        help="Initialize a repository.",
    )

    # ---------------------------------------------------------
    # hash-object
    # ---------------------------------------------------------

    hash_parser = subparsers.add_parser(
        "hash-object",
        help="Create a blob object from a file.",
    )

    hash_parser.add_argument(
        "file",
        help="File to hash.",
    )

    # ---------------------------------------------------------
    # cat-file
    # ---------------------------------------------------------

    cat_parser = subparsers.add_parser(
        "cat-file",
        help="Display a stored object.",
    )

    cat_parser.add_argument(
        "object_id",
        help="Object ID.",
    )

    # ---------------------------------------------------------
    # add
    # ---------------------------------------------------------

    add_parser = subparsers.add_parser(
        "add",
        help="Stage a file.",
    )

    add_parser.add_argument(
        "file",
        help="File to stage.",
    )

    # ---------------------------------------------------------
    # status
    # ---------------------------------------------------------

    subparsers.add_parser(
        "status",
        help="Display repository status.",
    )

    # ---------------------------------------------------------
    # commit
    # ---------------------------------------------------------

    commit_parser = subparsers.add_parser(
        "commit",
        help="Create a commit.",
    )

    commit_parser.add_argument(
        "-m",
        "--message",
        required=False,
    )

    commit_parser.add_argument(
        "--author",
        required=False,
    )

    # ---------------------------------------------------------
    # log
    # ---------------------------------------------------------

    subparsers.add_parser(
        "log",
        help="Display commit history.",
    )

    # ---------------------------------------------------------
    # diff
    # ---------------------------------------------------------

    subparsers.add_parser(
        "diff",
        help="Display working-tree differences.",
    )

    # ---------------------------------------------------------
    # branch
    # ---------------------------------------------------------

    branch_parser = subparsers.add_parser(
        "branch",
        help="List or create branches.",
    )

    branch_parser.add_argument(
        "name",
        nargs="?",
        help="New branch name.",
    )

    # ---------------------------------------------------------
    # checkout
    # ---------------------------------------------------------

    checkout_parser = subparsers.add_parser(
        "checkout",
        help="Switch branches.",
    )

    checkout_parser.add_argument(
        "branch",
        help="Branch to checkout.",
    )

    # ---------------------------------------------------------
    # merge
    # ---------------------------------------------------------

    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge a branch.",
    )

    merge_parser.add_argument(
        "branch",
        help="Branch to merge.",
    )

    # ---------------------------------------------------------
    # tag
    # ---------------------------------------------------------

    tag_parser = subparsers.add_parser(
        "tag",
        help="List or create tags.",
    )

    tag_parser.add_argument(
        "name",
        nargs="?",
        help="New tag name.",
    )

    # ---------------------------------------------------------
    # push
    # ---------------------------------------------------------

    push_parser = subparsers.add_parser(
        "push",
        help="Push to a remote repository.",
    )

    push_parser.add_argument(
        "remote",
        help="Remote repository path.",
    )

    push_parser.add_argument(
        "--branch",
        default=None,
        help="Branch to push. Defaults to current branch.",
    )

    # ---------------------------------------------------------
    # fetch
    # ---------------------------------------------------------

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch from a remote repository.",
    )

    fetch_parser.add_argument(
        "remote",
        help="Remote repository path.",
    )

    # ---------------------------------------------------------
    # pull
    # ---------------------------------------------------------

    pull_parser = subparsers.add_parser(
        "pull",
        help="Fetch and merge from a remote repository.",
    )

    pull_parser.add_argument(
        "remote",
        help="Remote repository path.",
    )

    pull_parser.add_argument(
        "--branch",
        default=None,
        help="Branch to pull. Defaults to current branch.",
    )

    # ---------------------------------------------------------
    # clone
    # ---------------------------------------------------------

    clone_parser = subparsers.add_parser(
        "clone",
        help="Clone a repository.",
    )

    clone_parser.add_argument(
        "remote",
        help="Source repository path.",
    )

    clone_parser.add_argument(
        "destination",
        help="Destination directory.",
    )

    # ---------------------------------------------------------
    # gc
    # ---------------------------------------------------------

    subparsers.add_parser(
        "gc",
        help="Remove unreachable objects.",
    )

    # ---------------------------------------------------------
    # pack
    # ---------------------------------------------------------

    subparsers.add_parser(
        "pack",
        help="Create a pack file.",
    )

    return parser


def handle_init(
    repository: RepositoryManager,
) -> None:
    """Handle init command."""

    repository.initialize()

    print(
        f"Initialized empty MyVCS repository in "
        f"{repository.metadata_directory}"
    )


def handle_hash_object(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    file_path: str,
) -> None:
    """Handle hash-object command."""

    repository.require_repository()

    source_path = (
        repository.working_directory
        / file_path
    ).resolve()

    if not source_path.is_file():
        raise MyVCSError(
            f"File does not exist: {file_path}"
        )

    data = source_path.read_bytes()

    blob = BlobObject(
        data=data,
        configuration=configuration,
    )

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    object_id = object_store.write(
        blob
    )

    print(object_id)


def handle_cat_file(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    object_id: str,
) -> None:
    """Handle cat-file command."""

    repository.require_repository()

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    data = object_store.read(
        object_id
    )

    print(
        data.decode(
            "utf-8",
            errors="replace",
        )
    )


def handle_add(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    file_path: str,
) -> None:
    """Handle add command."""

    repository.require_repository()

    service = AddService(
        repository=repository,
        configuration=configuration,
    )

    object_id = service.add(
        file_path
    )

    print(
        f"Staged {file_path} "
        f"({object_id})"
    )

##################################################old
''''
def handle_status(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle status command."""

    repository.require_repository()

    service = StatusService(
        repository=repository,
        configuration=configuration,
    )

    status = service.get_status()

    reference_manager = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    branch = (
        reference_manager.current_branch()
    )

    print(
        f"On branch {branch}"
    )

    print()

    if status["staged"]:
        print("Changes to be committed:")

        for path in status["staged"]:
            print(
                f"  staged: {path}"
            )

        print()

    if status["untracked"]:
        print("Untracked files:")

        for path in status["untracked"]:
            print(
                f"  untracked: {path}"
            )

        print()

    if (
        not status["staged"]
        and not status["untracked"]
    ):
        print(
            "Working tree clean."
        )

        '''''
############################################


def handle_status(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle status command."""

    repository.require_repository()

    service = StatusService(
        repository=repository,
        configuration=configuration,
    )

    status = service.get_status()

    reference_manager = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    branch = reference_manager.current_branch()

    print(
        f"On branch {branch}"
    )

    print()

    if status["staged"]:
        print("Changes to be committed:")

        for path in status["staged"]:
            print(
                f"  staged: {path}"
            )

        print()

    if status["modified"]:
        print("Changes not staged for commit:")

        for path in status["modified"]:
            print(
                f"  modified: {path}"
            )

        print()

    if status["deleted"]:
        print("Changes not staged for commit:")

        for path in status["deleted"]:
            print(
                f"  deleted: {path}"
            )

        print()

    if status["untracked"]:
        print("Untracked files:")

        for path in status["untracked"]:
            print(
                f"  untracked: {path}"
            )

        print()

    if (
        not status["staged"]
        and not status["modified"]
        and not status["deleted"]
        and not status["untracked"]
    ):
        print(
            "Working tree clean."
        )
def handle_commit(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    message: str | None,
    author: str | None,
) -> None:
    """Handle commit command."""

    repository.require_repository()

    commit_message = message or configuration.require(
        "commit",
        "default_message",
    )

    commit_author = author or configuration.require(
        "commit",
        "default_author",
    )

    service = CommitService(
        repository=repository,
        configuration=configuration,
    )

    commit_id = service.commit(
        message=commit_message,
        author=commit_author,
    )

    print(
        f"[{commit_id}] {commit_message}"
    )


def handle_log(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle log command."""

    repository.require_repository()

    reference_manager = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    commit_id = (
        reference_manager.get_head_commit()
    )

    if not commit_id:
        print("No commits yet.")
        return

    while commit_id:
        raw_object = object_store.read(
            commit_id
        )

        decoded = raw_object.decode(
            "utf-8",
            errors="replace",
        )

        print(
            f"commit {commit_id}"
        )

        print(decoded)
        print()

        parent_id = None

        for line in decoded.splitlines():
            if line.startswith("parent "):
                parent_id = line.removeprefix(
                    "parent "
                )
                break

        commit_id = parent_id


def handle_diff(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle diff command."""

    repository.require_repository()

    service = DiffService(
        repository=repository,
        configuration=configuration,
    )

    output = service.diff()

    if output:
        print(output)
    else:
        print("No differences.")


def handle_branch(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    branch_name: str | None,
) -> None:
    """Handle branch command."""

    repository.require_repository()

    service = BranchService(
        repository=repository,
        configuration=configuration,
    )

    if branch_name:
        service.create_branch(
            branch_name
        )

        print(
            f"Created branch '{branch_name}'."
        )

        return

    reference_manager = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    current_branch = (
        reference_manager.current_branch()
    )

    branches = service.list_branches()

    for branch in branches:
        marker = "*" if branch == current_branch else " "

        print(
            f"{marker} {branch}"
        )


def handle_checkout(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    branch_name: str,
) -> None:
    """Handle checkout command."""

    repository.require_repository()

    service = CheckoutService(
        repository=repository,
        configuration=configuration,
    )

    service.checkout(
        branch_name
    )

    print(
        f"Switched to branch '{branch_name}'."
    )


def handle_merge(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    branch_name: str,
) -> None:
    """Handle merge command."""

    repository.require_repository()

    service = MergeService(
        repository=repository,
        configuration=configuration,
    )

    commit_id = service.merge(
        branch_name
    )

    print(
        f"Merged '{branch_name}' "
        f"at {commit_id}."
    )


def handle_tag(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tag_name: str | None,
) -> None:
    """Handle tag command."""

    repository.require_repository()

    service = TagService(
        repository=repository,
        configuration=configuration,
    )

    if tag_name:
        service.create_tag(
            tag_name
        )

        print(
            f"Created tag '{tag_name}'."
        )

        return

    tags = service.list_tags()

    if not tags:
        print("No tags.")
        return

    for tag in tags:
        print(tag)


def _current_branch(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> str:
    """Return current branch."""

    references = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    branch = references.current_branch()

    if not branch:
        raise MyVCSError(
            "Unable to determine current branch."
        )

    return branch


def handle_push(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    remote_path: str,
    branch_name: str | None,
) -> None:
    """Handle push command."""

    repository.require_repository()

    branch = (
        branch_name
        or _current_branch(
            repository,
            configuration,
        )
    )

    service = RemoteService(
        repository=repository,
        configuration=configuration,
    )

    service.push(
        remote_path=remote_path,
        branch_name=branch,
    )

    print(
        f"Pushed branch '{branch}' "
        f"to '{remote_path}'."
    )


def handle_fetch(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    remote_path: str,
) -> None:
    """Handle fetch command."""

    repository.require_repository()

    service = RemoteService(
        repository=repository,
        configuration=configuration,
    )

    service.fetch(
        remote_path=remote_path
    )

    print(
        f"Fetched from '{remote_path}'."
    )


def handle_pull(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    remote_path: str,
    branch_name: str | None,
) -> None:
    """Handle pull command."""

    repository.require_repository()

    branch = (
        branch_name
        or _current_branch(
            repository,
            configuration,
        )
    )

    service = RemoteService(
        repository=repository,
        configuration=configuration,
    )

    service.pull(
        remote_path=remote_path,
        branch_name=branch,
    )

    print(
        f"Pulled branch '{branch}' "
        f"from '{remote_path}'."
    )


def handle_clone(
    configuration: ApplicationConfig,
    remote_path: str,
    destination_path: str,
) -> None:
    """Handle clone command."""

    service = CloneService(
        configuration=configuration,
    )

    service.clone(
        remote_path=remote_path,
        destination_path=destination_path,
    )

    print(
        f"Cloned '{remote_path}' "
        f"to '{destination_path}'."
    )


def handle_gc(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle gc command."""

    repository.require_repository()

    service = GarbageCollectionService(
        repository=repository,
        configuration=configuration,
    )

    removed = service.collect()

    print(
        f"Garbage collection complete. "
        f"Removed {removed} object(s)."
    )


def handle_pack(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Handle pack command."""

    repository.require_repository()

    pack_directory = Path(
        configuration.require(
            "pack",
            "directory",
        )
    )

    if not pack_directory.is_absolute():
        pack_directory = (
            repository.metadata_directory
            / pack_directory
        )

    pack_name = configuration.require(
        "pack",
        "default_name",
    )

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    objects: dict[str, bytes] = {}

    for directory in repository.objects_directory.iterdir():
        if not directory.is_dir():
            continue

        for object_file in directory.iterdir():
            if not object_file.is_file():
                continue

            object_id = (
                directory.name
                + object_file.name
            )

            try:
                raw_data = object_file.read_bytes()
            except OSError:
                LOGGER.warning(
                    "Unable to read object: %s",
                    object_file,
                )
                continue

            objects[object_id] = raw_data

    if not objects:
        print(
            "No objects available to pack."
        )
        return

    pack_file = PackFile(
        pack_directory=pack_directory,
        configuration=configuration,
    )

    created = pack_file.create(
        objects=objects,
        pack_name=pack_name,
    )

    print(
        f"Pack created: {created}"
    )


def main() -> int:
    """CLI application entry point."""

    configuration: ApplicationConfig | None = None

    try:
        configuration = load_configuration()

        configure_logging(
            configuration
        )

        parser = create_parser()

        arguments = parser.parse_args()

        repository = RepositoryManager(
            working_directory=Path.cwd(),
            configuration=configuration,
        )

        if arguments.command == "init":
            handle_init(
                repository
            )

        elif arguments.command == "hash-object":
            handle_hash_object(
                repository,
                configuration,
                arguments.file,
            )

        elif arguments.command == "cat-file":
            handle_cat_file(
                repository,
                configuration,
                arguments.object_id,
            )

        elif arguments.command == "add":
            handle_add(
                repository,
                configuration,
                arguments.file,
            )

        elif arguments.command == "status":
            handle_status(
                repository,
                configuration,
            )

        elif arguments.command == "commit":
            handle_commit(
                repository,
                configuration,
                arguments.message,
                arguments.author,
            )

        elif arguments.command == "log":
            handle_log(
                repository,
                configuration,
            )

        elif arguments.command == "diff":
            handle_diff(
                repository,
                configuration,
            )

        elif arguments.command == "branch":
            handle_branch(
                repository,
                configuration,
                arguments.name,
            )

        elif arguments.command == "checkout":
            handle_checkout(
                repository,
                configuration,
                arguments.branch,
            )

        elif arguments.command == "merge":
            handle_merge(
                repository,
                configuration,
                arguments.branch,
            )

        elif arguments.command == "tag":
            handle_tag(
                repository,
                configuration,
                arguments.name,
            )

        elif arguments.command == "push":
            handle_push(
                repository,
                configuration,
                arguments.remote,
                arguments.branch,
            )

        elif arguments.command == "fetch":
            handle_fetch(
                repository,
                configuration,
                arguments.remote,
            )

        elif arguments.command == "pull":
            handle_pull(
                repository,
                configuration,
                arguments.remote,
                arguments.branch,
            )

        elif arguments.command == "clone":
            handle_clone(
                configuration,
                arguments.remote,
                arguments.destination,
            )

        elif arguments.command == "gc":
            handle_gc(
                repository,
                configuration,
            )

        elif arguments.command == "pack":
            handle_pack(
                repository,
                configuration,
            )

        else:
            parser.print_help()

        return configuration.require(
            "cli",
            "success_exit_code",
        )

    except MyVCSError as exc:
        LOGGER.error(
            "Application error: %s",
            exc,
        )

        print(
            f"Error: {exc}",
            file=sys.stderr,
        )

        if configuration:
            return configuration.require(
                "cli",
                "error_exit_code",
            )

        return 1

    except Exception:
        LOGGER.exception(
            "Unexpected application error."
        )

        print(
            "Unexpected application error. "
            "Check the log file.",
            file=sys.stderr,
        )

        if configuration:
            return configuration.require(
                "cli",
                "error_exit_code",
            )

        return 1