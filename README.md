# Backend Challenge – Python

> You may also complete this challenge in
> [TypeScript](https://github.com/limehome/backend-challenge-typescript).

## Context

We would like you to help us with a small service that we have for handling bookings. A booking for us simply tells us which guest will be staying in which unit, and when they arrive and the number of nights that guest will be enjoying our amazing suites, comfortable beds, great snac.. apologies - I got distracted.

Bookings are at the very core of our business and it's important that we get these right - we want to make sure that guests always get what they paid for, and also trying to ensure that our unit are continually booked and have as few empty nights where no-one stays as possible. 

A unit is simply a location that can be booked, think like a hotel room or even a house. 

For the exercise today, we would like you to help us solve an issue we've been having with our example service, as well as implement a new feature to improve the code base. 

### You should help us:

Identify and fix a bug that we've been having with bookings - there seems to be something going wrong with the booking process where a guest will arrive at a unit only to find that it's already booked and someone else is there!
There are many ways to solve this bug - there is no single correct answer that we are looking for.

### Implement a new feature:

Allowing guests to extend their stays if possible. It happens that <strike>sometimes</strike> all the time people love staying at our locations so much that they want to extend their stay and remain there a while longer. We'd like a new API that will let them do that.

### Write handover notes:

To wrap things up, write a brief NOTES.md file to the root of the project. Imagine this is for a fellow engineer that will review your work and wants to understand your thoughts.

If you rewrote half the setup while adding a small feature, they will want to understand your reasoning.

Be mindful of their time. Write for humans, not AI. No bonus points for fancy formatting or verbosity, content counts.

### Keep in mind:

While this is an opportunity for you to showcase your skills, we also want to be respectful of your time and suggest spending no more than 1 hour on this.

We want to see you reaching the goal with minimal effort and maximum ownership. You are welcome to also leverage modern tooling including AI. But as in professional work, you are responsible for the code.

When implementing, make sure you follow known best practices around architecture, testability, and documentation.

Treat the code as your own and ensure you would be confident to hand over like this to another engineer. Does not need to be perfect, just "good enough".

## How to run

**Prerequisites:** docker

Start the server:

```shell
docker compose up
```

Run tests (one test intentionally fails — that's the bug to fix):

```shell
docker compose run --rm api uv run pytest
```

API docs: http://localhost:8000/docs
