#!/bin/bash
################################################################################
# File: buildscript.sh
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Builds the debian installation package for mailtools.
################################################################################

PROJECT_NAME='mailtools'
VERSION_NUM='1.3.0-stable'
ARCH='x86_64'
PACKAGE_NAME="$(echo $PROJECT_NAME)_$(echo $VERSION_NUM)_$ARCH"
PROJECT_DIR=$(dirname $(pwd))

# Clear out working directory
./clean.sh

ETC_DIR="/usr/lib/$PROJECT_NAME/etc"
BIN_DIR="/usr/lib/$PROJECT_NAME/bin"

# Make the package user library directory
mkdir -vp "$PACKAGE_NAME"
mkdir -vp "$PACKAGE_NAME/$ETC_DIR"
mkdir -vp "$PACKAGE_NAME/$BIN_DIR"

# Insert configuration files
cp -rvf DEBIAN $PACKAGE_NAME

################################################################################
# CONFIGURATION FILES --> placed in /usr/lib/mailtools/etc/
################################################################################

cp -rvf "$PROJECT_DIR/src/etc/config.yml" "$PACKAGE_NAME/$ETC_DIR"
cp -rvf "$PROJECT_DIR/src/etc/banner.txt" "$PACKAGE_NAME/$ETC_DIR"

################################################################################
# EXECUTABLES from src --> placed in /usr/lib/mailtools/bin/
################################################################################
# frontend
cp -rvf "$PROJECT_DIR/src/bin/mailtools.py" "$PACKAGE_NAME/$BIN_DIR"

# configuration scripts
cp -rvf "$PROJECT_DIR/src/bin/Config.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/user_setup.sh" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/user_teardown.sh" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/sudo_teardown.sh" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/arg_complete_mailtools.sh" "$PACKAGE_NAME/$BIN_DIR"

# database processing
cp -rvf "$PROJECT_DIR/src/bin/Process.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/NoSQL.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/Script.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/Search.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/Store.py" "$PACKAGE_NAME/$BIN_DIR"

# IF-THIS-THEN-THAT processing
cp -rvf "$PROJECT_DIR/src/bin/ifttt.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/ifttt_actions.py" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/ifttt_parse.py" "$PACKAGE_NAME/$BIN_DIR"

# cron wrapper
cp -rvf "$PROJECT_DIR/src/bin/mk_cronjob.sh" "$PACKAGE_NAME/$BIN_DIR"
cp -rvf "$PROJECT_DIR/src/bin/rm_cronjob.sh" "$PACKAGE_NAME/$BIN_DIR"

################################################################################
# DEBIAN BUILD --> Build the deb package and clear the build directory
################################################################################
dpkg-deb --build $PACKAGE_NAME
rm -rf $PACKAGE_NAME

printf "DONE!\n"

