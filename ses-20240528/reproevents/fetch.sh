#!/bin/sh

ssh reprostim@reproiner "cd reprostim/Events/data; ( head -n 1 2024-03-26T14:17:27-04:00.csv; grep 2024-05-28T11 2024-03-26T14:17:27-04:00.csv ); " > 2024-05-28T11.csv
