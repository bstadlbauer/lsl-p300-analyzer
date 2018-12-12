clear all, close all, clc

%% Test for data loading 

s1 = load('data/s1');

data = s1.s1.test;
target_ind = data(11, :) == 1;

target = data(10:11, target_ind);
