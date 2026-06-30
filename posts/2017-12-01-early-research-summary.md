---
title: Early Research Summary (pre-2018)
date: 2017-12-01
summary: An archived summary of my foundational work: noise benefits in statistical machine learning, Bayesian function approximation, and the early turn toward ML for policy.
tags: [research, machine-learning, archive]
draft: false
---

*This is an archived research summary from an earlier version of my website. It describes the foundational arc of my work and is kept here for reference.*

My research interests and output have always been varied. As a broad binning, about half of my work falls under statistical machine learning, and the other half under technology policy.

Most of my work focuses either on applying machine learning to problems in policy analysis, or on examining pathologies in the use of machine learning for decision-making. The latter includes work on fairness in the use of ML for decisions in social institutions: see, for example, this [RAND report](https://www.rand.org/pubs/research_reports/RR2708.html) or my [TEDx talk](https://www.youtube.com/watch?v=4l_LZ5NcIBI). The former includes identifying and developing ML tools better suited to policy and systems analysis, such as [fuzzy cognitive maps for the causal simulation of policy counterfactuals](https://arxiv.org/abs/1906.11247).

## Noise benefits in machine learning

I spent most of my doctoral and post-doctoral years on the theoretical foundations of statistical machine learning, specifically establishing stochastic-resonance (noise-benefit) phenomena in learning algorithms.

My dissertation ([summary chapter](/resumes/OsondeOsoba-DissertationPreview.pdf)) proved that the controlled injection of noise can improve the convergence time of Expectation-Maximization (EM) algorithms. This is an instance of a noise benefit, or stochastic resonance, in statistical signal processing. We call this noise-assisted improvement the [Noisy Expectation-Maximization (NEM) algorithm](http://sipi.usc.edu/~kosko/FNL-September-2013.pdf). Many iterative statistical estimation and learning algorithms are special cases of EM, so the noise-induced speed-up applies to them as well. The most notable such case is backpropagation training for neural networks (see this [paper](http://sipi.usc.edu/~kosko/N-BP-Neural-Networks-26June2020.pdf) with B. Kosko and K. Audhkhasi).

## Bayesian function approximation

I also worked on the effect of using approximate model functions (priors and likelihoods) in Bayesian inference. I proved that Bayes' theorem produces posterior densities whose approximation quality matches that of the underlying model-function approximations. This is the [Bayesian Approximation Theorem (BAT)](http://sipi.usc.edu/~kosko/SMC-B-Bayes-Fuzzy-Approximation-September-2011.pdf). I also demonstrated a robust method for approximating arbitrary priors or likelihoods of compact support, either from data or from expert input. The method represents bounded closed-form model functions exactly and efficiently, and so subsumes many traditional applications of Bayesian inference.

For a more comprehensive and current view of my work, see my [Google Scholar profile](https://scholar.google.com/citations?hl=en&user=w5oYjbYAAAAJ&view_op=list_works&sortby=pubdate).
