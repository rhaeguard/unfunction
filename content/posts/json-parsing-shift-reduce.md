+++
title = 'How to parse JSON using shift-reduce parsing approach'
date = 2023-10-31T23:32:33-06:00
draft = true
github = 'rhaeguard/gojson'
+++

[WIP]

There are a lot of (built-in and third-party) libraries in almost all languages that allow developers to parse JSON text into some format. In this tutorial, we are going to learn how this is actually done. 

### Grammar

Just like in natural languages, the programming languages and various data formats have certain syntax. The syntax is determined based on the grammar of the language/format. For JSON the following is a simplified version of a part of the grammar:

```plaintext
1. json ::= value
2. value ::= object | array | string
3. object ::= '{' members '}'
4. members ::= member | member ',' members
5. member ::= string ':' value
6. string ::= '"' characters '"'
```

Check out the full grammar [here](https://www.crockford.com/mckeeman.html), but we will also go over the grammar later. The format shown above is called the BNF or [Backus-Naur form](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form). Most programming languages have a BNF grammar. Each line in the grammar above is called a production rule. Anything that's in single quotes above is called a _terminal_ symbol. Terminal means that we can no longer expand that part of the rule to something else. The remaining ones are called _non-terminals_ and they will be expanded. The following is just an example of an expansion:

```go
value ::= object
value ::= '{' members '}' // apply rule 3
value ::= '{' member '}' // rule 4-1
value ::= '{' string ':' value '}' // rule 5
value ::= '{' string ':' string '}' // rule 2-3
value ::= '{' '"' characters '"' ':' string '}' // rule 6
value ::= '{' '"' name '"' ':' string '}' // chars expanded 
value ::= '{' '"' name '"' ':' '"' characters '"' '}' // rule 6
value ::= '{' '"' name '"' ':' '"' jane '"' '}' // chars expanded
```

Grammars show us the way the input is formatted. There are different methods of parsing. One of which is called _recursive descent_ or _top-down parsing_. In this type of parsing, we start from the first character of the input and recursively apply different production rules (like we did above) to create a tree structure. So, let's take a look at a simple example.

Assume this is our input:
```js
{"age": 37}
```

In recursive descent parsing, we'll start from the first character and try to apply production rules to create the tree. The process will unfold roughly this way:

0. we need to parse _value_, proceed with any rule that matches
1. `{` matches with _object_ rule, let's try to parse the rest as _members_
2. _members_ start with parsing a _member_
3. _member_ needs a string first, then colon and finally another value
4. well the next char is `"` and it matches with string rule, so parse as string until we meet another `"`
5. the next is colon, so that matches with our rule
6. we then have to parse a value (refer to step 0)
7. finally we encounter `}` 
    - which means the object rule is complete, 
    - which then completes the value rule, 
    - which then completes json

The most obvious feature of recusive descent is the fact that the code actually resembles the grammar. It is used to parse JSON in golang's [standard library](https://github.com/golang/go/blob/e73e25b624c37a936bb42f50a11f56297a4cd637/src/encoding/json/encode.go#L159). I've also written a [top-down JSON parser](https://github.com/rhaeguard/jsonx). 

Recursive descent/top-down parsing is awesome, but there are other ways of parsing as well. Bottom-up parsing is another approach that's extremely common. Especially with parser generators like [yacc](https://en.wikipedia.org/wiki/Yacc). As the name implies, in bottom-up parsing, we go from ground up. What this means is that we try to construct the parts of the parse tree that we know, and slowly grow the parse tree. For the example above, this could mean that we can construct a _string_ first, and based on those, we can recognize that we have a _member_, and then create _members_ and _object_ and finally end up with the root _json_. In this tutorial, we will use a bottom-up approach, namely shift-reduce, to parse JSON. We will use Golang, but the ideas can be coded in any language.

# Shift-Reduce Parsing