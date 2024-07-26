#!/bin/sh
set -eu

# Color codes
RED_BG='\033[41m'
GREEN_BG='\033[42m'
YELLOW_BG='\033[43m'
BLUE_BG='\033[44m'
MAGENTA_BG='\033[45m'
CYAN_BG='\033[46m'
BLACK='\033[30m'
RESET='\033[0m'

# Function to print colored messages
print_color() {
    printf "%b%s%b %s\n" "$1$BLACK" "$2" "$RESET" "$3"
}

# Function to get user confirmation
get_confirmation() {
    printf "%b%s%b %s" "$YELLOW_BG$BLACK" "$1" "$RESET" "[Y/n]: "
    read -r answer
    case "$answer" in
        [Nn]*)
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

# Function to preview version bump and get confirmation
preview_and_confirm_bump() {
    print_color "$BLUE_BG" "PREVIEW:" "Dry run of version bump with flag: $1"
    poetry version --next-phase "$1" --dry-run
    if get_confirmation "Do you want to proceed with this version bump?"; then
        poetry version --next-phase "$1"
        print_color "$GREEN_BG" "SUCCESS:" "Version bumped."
        return 0
    else
        print_color "$RED_BG" "ABORT:" "Version bump cancelled."
        return 1
    fi
}

# Function to commit changes
commit_changes() {
    if get_confirmation "Do you want to commit these changes?"; then
        git add pyproject.toml
        git commit -m "Bump version to $(poetry version -s)"
        print_color "$GREEN_BG" "SUCCESS:" "Changes committed."
    else
        print_color "$RED_BG" "ABORT:" "Commit cancelled. Exiting."
        exit 1
    fi
}

# Function to push changes
push_changes() {
    if get_confirmation "Do you want to push these changes?"; then
        git push
        print_color "$GREEN_BG" "SUCCESS:" "Changes pushed."
    else
        print_color "$MAGENTA_BG" "SKIP:" "Push skipped. Continuing."
    fi
}

# Main script
main() {
    if [ $# -ne 1 ]; then
        print_color "$RED_BG" "ERROR:" "Invalid number of arguments."
        print_color "$CYAN_BG" "USAGE:" "$0 --<flag>"
        print_color "$CYAN_BG" "FLAGS:" "patch, minor, major, prepatch, preminor, premajor, prerelease"
        exit 1
    fi

    flag="${1#--}"
    initial_version=$(poetry version -s)

    case "$flag" in
        patch|minor|major|prepatch|preminor|premajor|prerelease)
            if preview_and_confirm_bump "$flag"; then
                commit_changes
                push_changes
            else
                exit 1
            fi
            ;;
        *)
            print_color "$RED_BG" "ERROR:" "Invalid flag: $flag"
            exit 1
            ;;
    esac

    print_color "$BLUE_BG" "INFO:" "Performing additional prepatch bump"
    if preview_and_confirm_bump prepatch; then
        commit_changes
        push_changes
    else
        exit 1
    fi

    final_version=$(poetry version -s)
    print_color "$GREEN_BG" "COMPLETE:" "Version bumped from $initial_version to $final_version"
}

main "$@"