# Section 4 — the build

A short brief, not a tutorial. Once your prediction sheet is filled in and section 4 is
ticked, this is what closes it.

## Where this comes from

Drill 5 sent requests to `api.github.com` and had you predict, for each one, whose mistake a
given response would be. This build asks you to write the code that makes that same judgement
on its own — for requests you choose, against calls you have not already seen the answer to.

## What you are building

A command-line tool, written in Python, that talks to the GitHub API — the same API drill 5
talked to. It takes several repositories at once rather than one, and prints something useful
about each. The exact call you make is your choice; what matters is what the tool does with
whatever comes back.

Taking more than one at a time forces a decision, and it is better made deliberately than by
accident: when three of them work and the fourth does not, what does your tool do? Whatever you
decide, be ready to say why.

## What it has to handle

A real call to a real service can come back more than one way, and your tool has to handle
five of them, each on purpose and each visibly:

- **A success.** The call worked, and the tool prints what it found.
- **A thing that is not there.** You asked about a repository or user that does not exist, and
  the tool says so plainly — not a crash, not a silent nothing.
- **A mistake in what was sent.** Something about the request itself was wrong, and the tool
  says so in a way a reader can tell apart from the case above.
- **A problem on GitHub's end.** The service itself failed to handle the request, and the tool
  says so in a way a reader can tell apart from both cases above.
- **The rate limit.** Unauthenticated requests are capped per hour, and your tool has to
  recognise being throttled and say so, rather than reporting it as any of the other four.

Each of these needs a different, visible response — output a person reading the terminal can
tell apart from the others without opening your source. Deciding which of the five a given
response belongs to, and handling that case on purpose, is the exercise. One branch that
catches everything and prints "an error occurred" does not meet it.

One of the five you will not be able to make happen. GitHub is not going to fail on demand
because you need it to, and there is no flag that asks it to. Write that branch anyway, and
expect to write it without ever seeing it run.

## What you need

- `requests`, and nothing else beyond the Python standard library.
- A `requirements.txt` with `requests` pinned to a specific version, not left open. The pin is
  part of what you are delivering — be ready to say why you pinned it rather than leaving it
  loose.
- A virtual environment. The tool should run cleanly from a fresh clone, in a fresh `venv`,
  installing from `requirements.txt` alone.

## What you are not doing

No tests, and no dependency beyond `requests`.

## The two conditions

The same two conditions as the capstone at the end of your checklist, applied here first:

- Build it from an empty directory.
- Do not follow any single tutorial end to end.

Looking things up as you go is expected — that is the job. Following one guide from top to
bottom is a different activity, and it will not tell you what this build is for.

## How long this should take

An evening or two. If it is taking a weekend, you have picked up more than the brief asks for
— cut back rather than push through.

## What to submit

A pull request, from a feature branch, the same way as section 3. Put the link in your section
4 completion update on Discord, and bring it to your session.

## This is not the capstone

The capstone at the end of your checklist is also called "the build." It is a separate,
larger project, built later, and none of what it needs comes from this one beyond the same
delivery method — a pull request from a feature branch. Finishing this does not shorten the
capstone, and the capstone does not depend on anything here beyond the habit of building from
empty.
