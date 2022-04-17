#!/usr/bin/env bash
echo "START"

while getopts p:i:w: flag
do
    case "${flag}" in
        p) project_name=${OPTARG};;
        i) bug_id=${OPTARG};;
        w) work_dir=${OPTARG};;
    esac
done

bugsinpy_location="$(pwd)/BugsInPy"
project_location="$bugsinpy_location/projects/$project_name"

echo "src = $project_location/bugs/$bug_id/bug.info"
echo "dst = $work_dir/$project_name/bugsinpy_bug.info"

cp -f "$project_location/bugs/$bug_id/bug.info" "$work_dir/$project_name/bugsinpy_bug.info"
cp -f "$project_location/bugs/$bug_id/requirements.txt" "$work_dir/$project_name/bugsinpy_requirements.txt"
cp -f "$project_location/bugs/$bug_id/run_test.sh" "$work_dir/$project_name/bugsinpy_run_test.sh"
rm -f "$work_dir/$project_name/bugsinpy_setup.sh"
rm -f "$work_dir/$project_name/bugsinpy_compile_flag"
if [[ -e "$project_location/bugs/$bug_id/setup.sh" ]]; then
   cp -f "$project_location/bugs/$bug_id/setup.sh" "$work_dir/$project_name/bugsinpy_setup.sh"
fi

echo "END"