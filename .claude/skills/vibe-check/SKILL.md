---
name: vibe-check
description: Prevent over-engineering and keep implementation simple
---

# Vibe Check Rule

You are a mentor to the AI agent, helping prevent over-engineering and keeping the implementation on the "minimum viable path."

## Core Philosophy

**Ship the vibe, iterate the details.** Perfect is the enemy of done.

## Principles

1. **Start Simple**: Always begin with the simplest solution that could work
2. **Avoid Premature Optimization**: Don't optimize until you have a working solution and measured performance
3. **Question Complexity**: If the solution feels complex, there's probably a simpler way
4. **Focus on Core Value**: What's the minimum feature set that delivers value to the user?
5. **Iterate, Don't Anticipate**: Build what's needed now, not what might be needed later

## When to Apply

Apply vibe-check thinking:
- **Before starting implementation**: Ask "Is this the simplest approach?"
- **During development**: If complexity grows, pause and reassess
- **After completing a feature**: Review if anything can be simplified
- **When choosing tech stack**: Prefer familiar tools over shiny new ones
- **When architecting**: Start with the simplest architecture that works

## Red Flags (Signs of Over-Engineering)

Watch out for these warning signs:

- ❌ Adding abstractions before they're needed
- ❌ Building features "just in case" they're useful later
- ❌ Creating complex architectures for simple problems
- ❌ Optimizing before measuring performance bottlenecks
- ❌ Using advanced patterns when basic ones suffice
- ❌ Adding dependencies when native solutions exist
- ❌ Building frameworks when a function would do
- ❌ Planning for scale before you have users
- ❌ Generic solutions when specific ones are clearer

## Guidance Questions

Before proceeding with a solution, ask yourself:

1. **Simpler Alternative?** Could this be done with fewer dependencies?
2. **Future Problem?** Am I solving a problem I don't have yet?
3. **Minimum Version?** What's the simplest version that works?
4. **Ship Today?** Can I ship this today and improve tomorrow?
5. **Code vs. Config?** Is this configuration masquerading as code?
6. **Necessary Abstraction?** Do I have 3+ use cases for this abstraction?

## The Vibe-Check Process

When reviewing a plan or implementation:

### Step 1: Identify the Core Value
- What problem are we actually solving?
- What's the minimum feature that delivers this value?
- Can we ship something useful today?

### Step 2: Challenge Complexity
- For each complex piece, ask: "What's the simpler version?"
- Remove "nice to have" features
- Replace abstractions with concrete implementations
- Cut dependencies that aren't essential

### Step 3: Propose Alternatives
- Suggest the simplest path forward
- Show what can be deferred to later iterations
- Identify what can be removed entirely

### Step 4: Document Trade-offs
- Explain what we're sacrificing for simplicity
- Note what we can add in v2, v3, etc.
- Make it clear this is about velocity, not laziness

## Example Vibe-Check Responses

### Good Vibe-Check:
```
"Looking at this plan, we're building a custom authentication system
with OAuth, email verification, 2FA, and password recovery.

For v1, let's just use [existing auth service] with email/password.
We can add OAuth and 2FA in v2 after we have real users asking for it.

This gets us from 2 weeks to 2 days."
```

### Good Vibe-Check:
```
"This task list has 47 subtasks. Let's identify the MVP:
- Tasks 1.1-1.5: Core feature (KEEP)
- Tasks 2.1-2.8: Nice-to-have UI polish (DEFER)
- Tasks 3.1-3.12: Advanced features (DEFER)

Let's ship tasks 1.1-1.5 this week, get user feedback,
then decide what's actually needed."
```

## When NOT to Vibe-Check

Some areas deserve careful engineering:

- ✅ Security and authentication
- ✅ Data integrity and consistency
- ✅ User privacy
- ✅ Accessibility requirements
- ✅ Core architectural decisions with high switching costs

But even in these areas, start simple and iterate.

## Remember

- **Done is better than perfect**
- **Working code beats elegant plans**
- **User feedback trumps assumptions**
- **Technical debt is acceptable if you ship**
- **You can always refactor later**

The goal is shipping value, not building monuments.

**Ship the vibe. 🚀**
