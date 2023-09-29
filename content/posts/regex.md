+++
title = 'How to build a regex engine from scratch'
date = 2023-09-28T22:40:33-06:00
draft = true
+++

In this article, we'll build a simple regular expression engine that will be able to use `[a-zA-Z0–9_]+@[a-zA-Z0–9]+\.[a-zA-Z]{2,}` pattern to check for the validity of email addresses. I will use Golang. We'll divide the whole process into 3 sections:

- [Parsing](#parsing)
- [Building the epsilon-NFA](#building-the-epsilon-nfa)
- [Matching](#matching)

## Parsing
On its own, a regex string is just that - a string. We need to convert that input into something has a structure. In this section, we'll go over the process of parsing a regex string into tokens. 
The core idea when it comes to parsing regex is simple, we will look for the characters that have special meanings such as * + ? () [] {} etc. and will try to create tokens out of those. It'll be more clear once we start writing some code.
Before getting into the parsing algorithm, let's define some structs.

```go
type tokenType uint8

const (
 group           tokenType = iota
 bracket         tokenType = iota
 or              tokenType = iota
 quantifier      tokenType = iota
 literal         tokenType = iota
 groupUncaptured tokenType = iota
)

type token struct {
 tokenType tokenType
 // the payload required for each token will be different 
 // so we need to be flexible with the type
 value     interface{}
}

type parseContext struct {
 // the index of the character we're processing
 // in the regex string
 pos    int
 tokens []token
}
```

Now, next is our parsing algorithm

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

parseContext object is useful for us to keep track of our current position and save the already parsed tokens. So the basic idea is that we loop through each character and process it until we reach to the end of the regex string. Next, let's take a look at the process method. It's a bit more involved, so let's take it step by step.

```go
func process(regex string, ctx *parseContext) {
 ch := regex[ctx.pos]
 if ch == '(' {
    groupCtx := &parseContext{
     pos:    ctx.pos,
     tokens: []token{},
    }
    parseGroup(regex, groupCtx)
    ctx.tokens = append(ctx.tokens, token{
     tokenType: group,
     value:     groupCtx.tokens,
    })
 } else if ch == '[' {
    parseBracket(regex, ctx)
 } else if ch == '|' {
    parseOr(regex, ctx)
 } else if ch == '*' || ch == '?' || ch == '+' {
    parseRepeat(regex, ctx)
 } else if ch == '{' {
    parseRepeatSpecified(regex, ctx)
 } else {
    // literal
    t := token{
     tokenType: literal,
     value:     ch,
    }
  
    ctx.tokens = append(ctx.tokens, t)
 }
}
```
As we mentioned earlier, we try to match the characters we recognize and use them to parse tokens. Let's take the first if statement. We check if the character is ( - the opening parenthesis. It represents the start of a group. Thus we try to parse the next couple of characters expecting a string of characters that corresponds to a regex group. The same applies to all the other characters specified in conditions above. However, the steps following the match will be different for each character as they have different semantic meanings. Next, we'll examine each of the functions defined in the above snippet. 
Let's actually start from the very bottom because it's the simplest case. If the character is not recognized, then it probably is a literal. Please keep in mind that this is a simplified implementation. There are a lot of cases to consider when it comes to parsing regular expressions; for instance, 1 is a number, but depending on the context it can actually be a part of a backreference \1 that refers to the first captured group. Our simplified algorithm also does not consider the escape characters. 
Next, let's take a look at the parsing of group expressions. This is the implementation:

```go
func parseGroup(regex string, ctx *parseContext) {
   ctx.pos += 1 // get past the LPAREN (
   for regex[ctx.pos] != ')' {
    process(regex, ctx)
    ctx.pos += 1
   }
}
```

It's extremely simple, we process each character like we did in the parse method until we encounter the closing parenthesis. We will not cover the error handling in this tutorial, so we're simply not checking if the index is still within bounds. It will panic anyway. But what about the extra code around parseGroup ? What happens there? Here's the snippet:

```go
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

Basically, we create a new context specific to each group, so that we'll be able to bundle together all the tokens within a specific group without dealing with the top level context object. 
Let's now see how we can parse bracket expressions. This is the whole function, but we'll cover it step by step.

```go
func parseBracket(regex string, ctx *parseContext) {
   ctx.pos++ // get past the LBRACKET
   var literals []string
   for regex[ctx.pos] != ']' {
      ch := regex[ctx.pos]
    
      if ch == '-' {
         next := regex[ctx.pos+1]
         prev := literals[len(literals)-1][0]
         literals[len(literals)-1] = fmt.Sprintf("%c%c", prev, next)
         ctx.pos++
      } else {
         literals = append(literals, fmt.Sprintf("%c", ch))
      }
    
      ctx.pos++
   }
  
   literalsSet := map[uint8]bool{}
  
   for _, l := range literals {
    if len(l) == 1 {
       literalsSet[l[0]] = true
    } else {
       for i := l[0]; i <= l[1]; i++ {
          literalsSet[i] = true
       }
    }
   }
  
   ctx.tokens = append(ctx.tokens, token{
    tokenType: bracket,
    value:     literalsSet,
   })
}
```
Similarly to the way we parsed the group expression, we go through each character till we reach the closing bracket character. For each character we check if it is - because that's the range indicator (e.g., a-zK-Z2-8). If it's not the range indicator we consider it a single literal, and save it to the list.

```go
var literals []string
for regex[ctx.pos] != ']' {
  ch := regex[ctx.pos]

  if ch == '-' {
     next := regex[ctx.pos+1]
     prev := literals[len(literals)-1][0]
     literals[len(literals)-1] = fmt.Sprintf("%c%c", prev, next)
     ctx.pos++
  } else {
     literals = append(literals, fmt.Sprintf("%c", ch))
  }

  ctx.pos++
}
```

When it is indeed the range indicator, we take the next character from the regex string, and the previous character from the list of literals (it's the last character in that list). Then we save it back to the list as 2 characters together. We could choose a different way of saving the parsed literals, but I find this to be simple and easy to understand.
Moving on, now we have a list of literals and ranges. But those can contain duplicates. Consider the following regex: [a-me-s] . There's a clear overlap between the ranges.

```go
literalsSet := map[uint8]bool{}
  
for _, l := range literals {
  if len(l) == 1 {
     literalsSet[l[0]] = true
  } else {
     for i := l[0]; i <= l[1]; i++ {
        literalsSet[i] = true
     }
  }
}

ctx.tokens = append(ctx.tokens, token{
  tokenType: bracket,
  value:     literalsSet,
})
```

This part of the algorithm is pretty simple, we go over the saved values, and check if they are literals or ranges. If ranges we go over each character in the range and add it to the set. By definition, sets do not contain duplicates, so that gets job done. Since we're implementing this in Golang, we are using a map because there are no natively provided sets in Golang, and installing a library just for a set is unnecessary. Finally, once we have all the duplicates removed, we save the bracket token to our list of tokens.

## Building the epsilon-NFA

## Matching