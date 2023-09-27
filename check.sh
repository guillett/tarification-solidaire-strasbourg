#!/bin/zsh

set +e

for i in **/*.ipynb
do
    echo $i
    #jupyter execute "$i"
    # if [[ $? -ne 0 ]]; then
    #     echo $i
    #     break
    # fi
    jupyter nbconvert --clear-output --inplace "$i"
done
