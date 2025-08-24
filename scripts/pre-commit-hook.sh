#!/bin/bash

# Pre-commit hook to prevent secret commits
# This script checks for common patterns that might indicate secrets

echo "🔍 Running pre-commit security checks..."

# Patterns that might indicate secrets
SECRET_PATTERNS=(
    "password.*=.*['\"][^'\"]*['\"]"
    "secret.*=.*['\"][^'\"]*['\"]"
    "key.*=.*['\"][^'\"]*['\"]"
    "token.*=.*['\"][^'\"]*['\"]"
    "api_key.*=.*['\"][^'\"]*['\"]"
    "private_key.*=.*['\"][^'\"]*['\"]"
    "ssh.*=.*['\"][^'\"]*['\"]"
    "aws.*=.*['\"][^'\"]*['\"]"
    "database.*=.*['\"][^'\"]*['\"]"
    "connection.*=.*['\"][^'\"]*['\"]"
)

# File extensions to check
FILE_EXTENSIONS=("py" "js" "json" "yaml" "yml" "env" "sh" "bash" "txt" "md")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a file contains potential secrets
check_file_for_secrets() {
    local file="$1"
    local found_secrets=false
    
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if grep -i -E "$pattern" "$file" > /dev/null 2>&1; then
            echo -e "${RED}❌ Potential secret found in $file${NC}"
            echo -e "${YELLOW}   Pattern: $pattern${NC}"
            grep -i -E "$pattern" "$file" | head -3
            found_secrets=true
        fi
    done
    
    if [ "$found_secrets" = true ]; then
        return 1
    fi
    return 0
}

# Function to check for common secret file names
check_for_secret_files() {
    local found_secret_files=false
    
    # Check for common secret file patterns
    for file in .env* *.pem *.key *.crt *.p12 *.pfx id_rsa* *.ppk; do
        if [ -f "$file" ]; then
            echo -e "${RED}❌ Secret file detected: $file${NC}"
            found_secret_files=true
        fi
    done
    
    if [ "$found_secret_files" = true ]; then
        return 1
    fi
    return 0
}

# Get staged files
staged_files=$(git diff --cached --name-only)

if [ -z "$staged_files" ]; then
    echo -e "${GREEN}✅ No files staged for commit${NC}"
    exit 0
fi

echo "📁 Checking staged files for potential secrets..."

# Check each staged file
for file in $staged_files; do
    # Skip if file doesn't exist (might be deleted)
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Get file extension
    extension="${file##*.}"
    
    # Check if file extension is in our list
    for ext in "${FILE_EXTENSIONS[@]}"; do
        if [ "$extension" = "$ext" ]; then
            if ! check_file_for_secrets "$file"; then
                echo -e "${RED}🚫 Commit blocked due to potential secrets in $file${NC}"
                echo -e "${YELLOW}Please review and remove any hardcoded secrets before committing.${NC}"
                echo -e "${YELLOW}Use environment variables or GitHub secrets instead.${NC}"
                exit 1
            fi
            break
        fi
    done
done

# Check for secret files
if ! check_for_secret_files; then
    echo -e "${RED}🚫 Commit blocked due to secret files detected${NC}"
    echo -e "${YELLOW}Please remove secret files from staging area.${NC}"
    echo -e "${YELLOW}Add them to .gitignore if they should be ignored.${NC}"
    exit 1
fi

# Check for large files that might contain secrets
for file in $staged_files; do
    if [ -f "$file" ]; then
        file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 1048576 ]; then  # 1MB
            echo -e "${YELLOW}⚠️  Large file detected: $file (${file_size} bytes)${NC}"
            echo -e "${YELLOW}   Consider if this file should be committed${NC}"
        fi
    fi
done

echo -e "${GREEN}✅ Pre-commit security checks passed${NC}"
echo -e "${GREEN}✅ No secrets detected in staged files${NC}"
exit 0
