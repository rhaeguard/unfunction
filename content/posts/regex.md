+++
title = '[WIP] How to build a regex engine from scratch'
date = 2023-09-28T22:40:33-06:00
draft = false
+++

In this article, we'll build a simple regular expression engine that will be able to use `[a-zA-Z0–9_]+@[a-zA-Z0–9]+.[a-zA-Z]{2,}` pattern to check for the validity of email addresses. We will use Golang. The article is divided into 3 sections:

- [Parsing](#parsing)
- [Building the epsilon-NFA](#building-the-epsilon-nfa)
- [Matching](#matching)

## Parsing
On its own, a regex string is just that - a string. We need to convert that input into something has a structure. For instance:

```python
# original regex string
[a-zA-Z0–9_]+@[a-zA-Z0–9]+.[a-zA-Z]{2,}

# regex tokens
Repeat(1, infinity):
   Range(a, b,...z, A, B,...,Z, 0,...,9,_)
Literal(@)
Repeat(1, infinity):
   Range(a, b,...z, A, B,...,Z, 0,...,9)
Literal(.)
Repeat(2, infinity):
   Range(a, b,...z, A, B,...,Z)
```


In this section, we'll go over the process of parsing a regex string into tokens. 
The core idea when it comes to parsing regex is simple, we will look for the characters that have special meanings such as `* + ? () [] {}` etc. and will try to create tokens out of those. It'll be more clear once we start writing some code.
Before getting into the parsing algorithm, let's define some types and constants.

```go
type tokenType uint8 // <1>

const ( // <2>
   group           tokenType = iota
   bracket         tokenType = iota
   or              tokenType = iota
   repeat          tokenType = iota
   literal         tokenType = iota
   groupUncaptured tokenType = iota
)

type token struct { // <3>
   tokenType tokenType
   // the payload required for each token will be different 
   // so we need to be flexible with the type
   value     interface{}
}

type parseContext struct { // <4>
   // the index of the character we're processing
   // in the regex string
   pos    int
   tokens []token
}
```

1. it's just a type alias for the character type
2. constants for specifying the type of the token we are working with
3. the main token struct, it has a _type_ and a _value_ which can be anything depending on the given type
4. `parseContext` will help us keep track of our positions and will hold the tokens parsed so far

Now, next is our parsing algorithm:

```go
func parse(regex string) *parseContext {
   ctx := &parseContext{
      pos:    0,
      tokens: []token{},
   }
   for ctx.pos < len(regex) {
      process(regex, ctx)
      ctx.pos++
   }
  
   return ctx
}
```

The basic idea is that we loop through each character and process it until we reach to the end of the regex string. Next, let's take a look at the `process` method. It's a bit more involved, so let's take it step by step.

```go
func process(regex string, ctx *parseContext) {
	ch := regex[ctx.pos]
	if ch == '(' { // <1>
		groupCtx := &parseContext{
			pos:    ctx.pos,
			tokens: []token{},
		}
		parseGroup(regex, groupCtx)
		ctx.tokens = append(ctx.tokens, token{
			tokenType: group,
			value:     groupCtx.tokens,
		})
	} else if ch == '[' { // <2>
		parseBracket(regex, ctx)
	} else if ch == '|' { // <3>
		parseOr(regex, ctx)
	} else if ch == '*' || ch == '?' || ch == '+' { // <4>
		parseRepeat(regex, ctx)
	} else if ch == '{' { // <5>
		parseRepeatSpecified(regex, ctx)
	} else { // <6>
		// literal
		t := token{
			tokenType: literal,
			value:     ch,
		}

		ctx.tokens = append(ctx.tokens, t)
	}
}
```
As we mentioned earlier, we try to match the characters we recognize and use them to parse tokens.

1. if the current character is `(` - the opening parenthesis, we know that it needs to be a regex group, thus we try to parse the next couple of characters expecting a string of characters that corresponds to a regex group.
2. if it's `[` - the opening bracket, we know that it's a bracket expression, so we proceed accordingly
3. if the character is a vertical pipe - `|`, that's an Or expression (alternative). 
4. the characters `*`, `+` and `?` all represent repetition. I know that `?` means optional, but in terms of repetition, it simply means that the character repeats at most once.
5. curly braces specify repetition as well. In fact, the previous repetition options can all be specified using braces:
   - `a* == a{0,}`
   - `a+ == a{1,}`
   - `a? == a{0,1}`
6. if the character did not match with anything, we consider it as a literal. Please keep in mind that this is a simplified implementation. There are a lot of cases to consider when it comes to parsing regular expressions; for instance, 1 is a literal, but depending on the context it can actually be a part of a backreference `\1` that refers to the first captured group. Our simplified algorithm also DOES NOT consider the escape characters (which means `\a` is considered as a concatenation of two literals: `\` and `a`).

Next, we'll examine each of the functions defined in the above snippet. Let's start with the parsing of group expressions **_(1)_**:

```go
func parseGroup(regex string, ctx *parseContext) {
   ctx.pos += 1 // get past the LPAREN (
   for regex[ctx.pos] != ')' {
      process(regex, ctx)
      ctx.pos += 1
   }
}
```

We process each character like we did in the parse method until we encounter the closing parenthesis. We will not cover the error handling in this tutorial, so we're simply not checking if the index is still within bounds. It will panic anyway. But what about the extra code around `parseGroup` in the `process` function? What happens there? Here's the snippet:

```go
// snippet from the `process` function
groupCtx := &parseContext{
   pos:    ctx.pos,
   tokens: []token{},
}

// parsing
parseGroup(regex, groupCtx)

ctx.tokens = append(ctx.tokens, token{
   tokenType: group,
   value:     groupCtx.tokens,
})
```

We create a new context specific to each group, so that we'll be able to bundle together all the tokens within a specific group without dealing with the top level context object. 

Let's now see how we can parse bracket expressions **_(2)_**. This is the whole function, but we'll cover it step by step.

```go
func parseBracket(regex string, ctx *parseContext) {
	ctx.pos++ // get past the LBRACKET
	var literals []string
	for regex[ctx.pos] != ']' { // <1>
		ch := regex[ctx.pos]

		if ch == '-' { // <2>
			next := regex[ctx.pos+1]
			prev := literals[len(literals)-1][0] // <2-1>
			literals[len(literals)-1] = fmt.Sprintf("%c%c", prev, next) // <2-2>
			ctx.pos++
		} else { // <3>
			literals = append(literals, fmt.Sprintf("%c", ch))
		}

		ctx.pos++ // <4>
	}

	literalsSet := map[uint8]bool{}

	for _, l := range literals { // <5>
		for i := l[0]; i <= l[len(l)-1]; i++ { // <6>
			literalsSet[i] = true
		}
	}

	ctx.tokens = append(ctx.tokens, token{ // <7>
		tokenType: bracket,
		value:     literalsSet,
	})
}
```

1. Similarly to the way we parsed the group expression, we go through each character till we reach the closing bracket character (`]`). 
2. For each character we check if it is `-` because that's the range indicator (e.g., `a-zK-Z2-8`). 
   1. When it is indeed the range indicator, we take the next character from the regex string, and the previous character from the list of literals (_it's the last character in that list_). 
   2. Then we save it back to the list as 2 characters together. We could choose a different way of saving the parsed literals, but I find this to be simple and easy to understand.
3. If it's not the range indicator we consider it a single literal, and save it to the list.
4. Move on to the next character
5. `literals` list contains both literals and ranges. But those may contain duplicates. Consider the following regex: `[a-me-s]` . There's a clear overlap between the ranges. We go over the saved values and each literal to the `literalsSet`. By definition, sets do not contain duplicates, so that gets the job done. Since we're implementing this in Golang, we are using a map because there are no natively provided sets in Golang, and installing a library just for a set is unnecessary. 
6. Add each character from the start till the end of the saved value.
   1. In single literals, this will only add the literal itself
   2. In ranges, it will add everything from the first character till the last character (inclusive).
7. Finally, once we have all the duplicates removed, we save the bracket token to our list of tokens.

Next in line is `parseOr` which is able to parse alternations **_(3)_**.

```go
func parseOr(regex string, ctx *parseContext) {
	// <1:start>
	rhsContext := &parseContext{
		pos:    ctx.pos,
		tokens: []token{},
	}
	rhsContext.pos += 1 // get past |
	for rhsContext.pos < len(regex) && regex[rhsContext.pos] != ')' {
		process(regex, rhsContext)
		rhsContext.pos += 1
	}
	// <1:end>

	// both sides of the OR expression
	left := token{
		tokenType: groupUncaptured,
		value:     ctx.tokens, // <2>
	}

	right := token{ // <3>
		tokenType: groupUncaptured,
		value:     rhsContext.tokens,
	}
	ctx.pos = rhsContext.pos // <4>

	ctx.tokens = []token{{ // <5>
		tokenType: or,
		value:     []token{left, right},
	}}
}
```

1. The alternation (_or_) operation has the following syntax: `<left>|<right>` or `(<left>|<right>)` meaning it is an alternation between what's in the left hand side and what's on the right hand side. By the time we encounter the `|` symbol, we've already parsed everything to the left of it. Now, it's time to parse everything to the right. It's almost the same code as parsing groups.  We create a right-hand-side specific empty context, and collect all the tokens into it. We do this until the end of the regex string or until we face a closing parenthesis. 
2. Now that we are done parsing both sides, it's time to create the alternation token. The left side will contain all the tokens that were in the original context object, because it contains all the tokens we have parsed so far. 
3. For the right hand side, we take all the tokens collected into the `rhsContext` object. For both tokens, we use `groupUncaptured` as the type, it's simply a type created to denote a bundle of tokens.
4. We update the position of the original context.
5. We create the alternation token and add it to the original context. One important thing is that we do not keep the old tokens in the original context as they are already contained in the alternation token.

Now let's look at repetitions **_(4)_**.

```go
func parseRepeat(regex string, ctx *parseContext) {
	ch := regex[ctx.pos]
	var min, max int
	if ch == '*' {
		min = 0
		max = repeatInfinity
	} else if ch == '?' {
		min = 0
		max = 1
	} else {
		// ch == '+'
		min = 1
		max = repeatInfinity
	}
	// we need to wrap the last token with the quantifier data
	// so that we know what the min and max apply to
	lastToken := ctx.tokens[len(ctx.tokens)-1]
	ctx.tokens[len(ctx.tokens)-1] = token{
		tokenType: repeat,
		value: repeatPayload{
			min:   min,
			max:   max,
			token: lastToken,
		},
	}
}
```

- Basic idea for this particular method is that each symbol here specifies some minimum and maximum number of repetitions. `repeatInfinity` is `-1`, but we use it as infinity. 
- Once we have the boundaries set, we simply take  the last parsed token, wrap it in a `repeat` token and appropriate boundaries, and finally save it back to the same position in the tokens list. 

The other repetition expression has a bit longer code, but the idea is still the same **_(5)_**.

```go
func parseRepeatSpecified(regex string, ctx *parseContext) {
	// +1 because we skip LCURLY { at the beginning
	start := ctx.pos + 1
	// proceed until we reach to the end of the curly braces
	for regex[ctx.pos] != '}' {
		ctx.pos++
	}

	boundariesStr := regex[start:ctx.pos] // <1>
	pieces := strings.Split(boundariesStr, ",") // <2>
	var min, max int
	if len(pieces) == 1 { // <3>
		if value, err := strconv.Atoi(pieces[0]); err != nil {
			panic(err.Error())
		} else {
			min = value
			max = value
		}
	} else if len(pieces) == 2 { // <4>
		if value, err := strconv.Atoi(pieces[0]); err != nil {
			panic(err.Error())
		} else {
			min = value
		}

		if pieces[1] == "" {
			max = repeatInfinity
		} else if value, err := strconv.Atoi(pieces[1]); err != nil {
			panic(err.Error())
		} else {
			max = value
		}
	} else {
		panic(fmt.Sprintf("There must be either 1 or 2 values specified for the quantifier: provided '%s'", boundariesStr))
	}

	// we need to wrap the last token with the quantifier data
	// so that we know what the min and max apply to
	// <5>
	lastToken := ctx.tokens[len(ctx.tokens)-1]
	ctx.tokens[len(ctx.tokens)-1] = token{
		tokenType: repeat,
		value: repeatPayload{
			min:   min,
			max:   max,
			token: lastToken,
		},
	}
}
```

1. We need to get the string expression for boundaries which is everything between the curly braces `{}`.
2. Next, we split that string into pieces separated by a comma `,`
3. If there's only one element (e.g., `{1}`) that means the exact number of repeats, so `min` and `max` will be the same. The error handling syntax of Golang may make things look complicated, but it just means that if there's any error while converting a string into a integer, just panic and stop everything.
4. If there are two pieces, the first value is the min, and the second one is the max (e.g., `{3,7}`). However, there's a chance that the second value might be missing: `{3,}`. In this example, the token is required to repeat at least three times, but no upper bound is set which means it will be `repeatInfinity`. The error handling is the same as in `parseRepeat` function.
5. Now that we have the boundaries, we take  the last parsed token, wrap it in a `repeat` token and appropriate boundaries, and save it back to the same position in the tokens list. 

With this, we conclude the steps required for parsing a regex string. Next, we'll examine how we can build a state machine out of those tokens we've parsed.

## Building the epsilon-NFA

### What's an NFA?

WIP

### Regular expression to epsilon-NFA

The previous step provides us with a list of tokens. We now need to convert these an epsilon-NFA. To achieve this, we will use an algorithm called Thompson's construction. We'll explain the algorithm with several visual examples and the corresponding code. But before we do that, let's go over the structure of the overall algorithm.

To represent an NFA state, we'll use this simple structure:

```go
type state struct {
	start       bool
	terminal    bool
	transitions map[uint8][]*state
}
```

1. `start` indicates whether the state's the entrypoint or not.
2. `terminal` indicates wheteher the state's the final state. Reaching this state means that the input matches with the regex.
3. `transitions` is a map where a character maps to a list of different states.

This is the high-level visualization of the algorithm:

![Creating an NFA from regular expression, high level view](/unfunction/toNFA_explained.png)

- We will have a start (pink) and terminal (blue) states.
- For each token, we'll create a separate NFA, and these NFAs will be concatenated with epsilon transitions. Last state of the previous NFA, will be connected to the first state of the next NFA, like this:

![Concatenation process](/unfunction/toNFA_concat.png)

- There will be an epsilon transition from the start state to the first state (s1) of the concatenated NFAs.
- There will be an epsilon transition from the last state of the concatenated NFAs to the terminal state.

Let's go over the same thing in code:

```go
const epsilonChar uint8 = 0 // empty character

func toNfa(ctx *parseContext) *state {
	startState, endState := tokenToNfa(&ctx.tokens[0]) // <1>

	for i := 1; i < len(ctx.tokens); i++ { // <2>
		startNext, endNext := tokenToNfa(&ctx.tokens[i]) // <3>
		endState.transitions[epsilonChar] = append(endState.transitions[epsilonChar], startNext) // <4>
		endState = endNext // <5>
	}

	start := &state{ // <6>
		transitions: map[uint8][]*state{
			epsilonChar: {startState},
		},
		start: true,
	}
	end := &state{ // 7
		transitions: map[uint8][]*state{},
		terminal:    true,
	}

	endState.transitions[epsilonChar] = append(endState.transitions[epsilonChar], end) // <8>

	return start // <9>
}
```

1. We take the first token, and convert that to an NFA. `tokenToNfa` function will be explained later. For now, just know that it creates an NFA from the given token, and returns the start and end states of this newly created NFA.
2. We go over the rest of tokens
3. We call `tokenToNfa` for each token and save the start and end states.
4. We link the end state from the previous `tokenToNfa` call to the start state of the new NFA.
5. Save the end state, because it will be useful in the next iteration
6. We create the previously mentioned start state. This state now has an epsilon transition to the start state of the very first NFA we created. 
7. We create the terminal state. 
8. The end state of the last NFA we created now has an epsilon transition to the terminal state.
9. Finally, we return the start state because that's the entrypoint.

Now that we have an overall outline of what we're doing to construct our NFA, let's take a look at how each token is converted into an NFA.

```go
// returns (start, end)
func tokenToNfa(t *token) (*state, *state) {
	start := &state{
		transitions: map[uint8][]*state{},
	}
	end := &state{
		transitions: map[uint8][]*state{},
	}

	switch t.tokenType {
	case literal:
	case or:
	case bracket:
	case group, groupUncaptured:
	case repeat:
	default:
		panic("unknown type of token")
	}

	return start, end
}
```
- The code above is the skeleton of the `tokenToNfa` function, we'll go over each token type and how it is handled.
- Overall, we create empty `start` and `end` states, perform some logic within switch statement, and return those variables.

In the next couple of sections, we'll go over each token type, visualize the steps and finally show the code.

#### Literals

Let's start with the literals as they are the simplest to explain.

![literal to nfa](/unfunction/tokenToNfa_literal.png)

- In order to go from `start` to `end`, we need the transition `ch`. `ch` represents a single character.

```go
case literal:
	ch := t.value.(uint8)
	start.transitions[ch] = []*state{end}
```
- We can see the exact same thing in the code as well. `t.value` is referring to the value we saved in the `token` struct back when we were parsing the tokens.

#### or/alternative

![or to nfa](/unfunction/tokenToNfa_or.png)

- Or means a choice between two different paths. Recall that in the parsing phase, the value for or token had _left_ and _right_ sides (shown in the diagram as well). Each of these tokens represent different NFAs. 
- To create the Or NFA, we need to have:
	- an epsilon transition from the start state to the starts of both left and right NFAs
	- an epsilon transition from the ends of both left and right NFAs to the end state.

```go
case or:
	values := t.value.([]token)
	left := values[0]
	right := values[1]

	s1, e1 := tokenToNfa(&left) // <1>
	s2, e2 := tokenToNfa(&right) // <1>

	start.transitions[epsilonChar] = []*state{s1, s2} // <2>
	e1.transitions[epsilonChar] = []*state{end} // <3>
	e2.transitions[epsilonChar] = []*state{end} // <3>
```

1. Creating both left and right NFAs
2. Connecting the start state with the starts of both NFAs with an epsilon transition
3. Connecting the end states of each NFA with the end state of the Or NFA.

## Matching

## References

- https://en.wikipedia.org/wiki/Thompson%27s_construction
- https://en.wikipedia.org/wiki/Regular_expression
- https://deniskyashif.com/2019/02/17/implementing-a-regular-expression-engine/
- https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expressions
- https://regex101.com/
- https://github.com/python/cpython/blob/main/Lib/test/re_tests.py
- https://blog.cernera.me/converting-regular-expressions-to-postfix-notation-with-the-shunting-yard-algorithm/
- https://en.wikipedia.org/wiki/Shunting_yard_algorithm
- https://gobyexample.com/