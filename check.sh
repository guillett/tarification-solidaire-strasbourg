#!/bin/zsh

set +e

for i in **/*.ipynb
do
    #jupyter execute "$i"
    echo $i
    # if [[ $? -ne 0 ]]; then
    #     echo $i
    #     break
    # fi
    jupyter nbconvert --clear-output --inplace "$i"
done
