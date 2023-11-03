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

Recursive descent/top-down parsing is awesome, but there are other ways of parsing as well. Bottom-up parsing is another approach that's extremely common. Especially with parser generators like [yacc](https://en.wikipedia.org/wiki/Yacc). As the name implies, in bottom-up parsing, we go from ground up. What this means is that we try to construct the parts of the parse tree that we know, and slowly grow the parse tree. For the example above, this could mean that we can construct a _string_ first, and based on those, we can recognize that we have a _member_, and then create _members_ and _object_ and finally end up with the root _json_. In this tutorial, we will use a bottom-up approach, namely shift-reduce, to parse JSON. We will use Golang, but the concepts can be coded in any language.

# Shift-Reduce Parsing

The shift-reduce parsing approach is a table-driven parsing approach that consists of 2 operations - shift and reduce. Here's the simplified version of the algorithm:

```plaintext
init:
    0. the input to be parsed
    1. the parse table (PT)
    2. the parse stack (PS)
process:
    3. read the next lookahead(LA) from input
    4. does the combination of top element(s) of PS and LA 
       match with anything in PT?
        5. yes, read the action from PT, if the action is:
            5.1 shift - push LA to PS
            5.2 reduce - replace the combination with
                        the production rule specified
                        in the PT
        6. no, that's a parsing error, goto failure
    7. if the input is fully consumed and the PS is empty
       then goto return
    8. goto step 3
```

There are more nuances, of course, but the above algorithm captures the main idea of the concept. The biggest challenge of implementing this algorithm is to create the parse table. Below is a very simple grammar and its parse tree taken from [Wikipedia](https://en.wikipedia.org/wiki/LR_parser).

**Grammar:**

1. E → E * B
2. E → E + B
3. E → B
4. B → 0
5. B → 1

It is able to parse expressions such as 1+1 or 1*1+0.

**The Parse Tree:**

{{<raw_html>}}
<table>
    <thead>
        <tr>
            <th>state</th>
            <th colspan="5">action</th>
            <th colspan="2">goto</th>
        </tr>
        <tr>
            <th></th>
            <th>*</th>
            <th>+</th>
            <th>0</th>
            <th>1</th>
            <th>$</th>
            <th>E</th>
            <th>B</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th>0</td>
            <td></td>
            <td></td>
            <td>s1</td>
            <td>s2</td>
            <td></td>
            <td>3</td>
            <td>4</td>
        </tr>
        <tr>
            <th>1</td>
            <td>r4</td>
            <td>r4</td>
            <td>r4</td>
            <td>r4</td>
            <td>r4</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <th>2</td>
            <td>r5</td>
            <td>r5</td>
            <td>r5</td>
            <td>r5</td>
            <td>r5</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <th>3</td>
            <td>s5</td>
            <td>s6</td>
            <td></td>
            <td></td>
            <td>acc</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <th>4</td>
            <td>r3</td>
            <td>r3</td>
            <td>r3</td>
            <td>r3</td>
            <td>r3</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <th>5</td>
            <td></td>
            <td></td>
            <td>s1</td>
            <td>s2</td>
            <td></td>
            <td></td>
            <td>7</td>
        </tr>
        <tr>
            <th>6</td>
            <td></td>
            <td></td>
            <td>s1</td>
            <td>s2</td>
            <td></td>
            <td></td>
            <td>8</td>
        </tr>
        <tr>
            <th>7</td>
            <td>r1</td>
            <td>r1</td>
            <td>r1</td>
            <td>r1</td>
            <td>r1</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <th>8</th>
            <td>r2</td>
            <td>r2</td>
            <td>r2</td>
            <td>r2</td>
            <td>r2</td>
            <td></td>
            <td></td>
        </tr>
    </tbody>
</table>
{{</raw_html>}}

- `rn` is reducing to the rule number `n`
- `sn` is shifting the lookahead and moving to state `n`
- `acc` indicates successful parsing
- goto column indicates which state to move into
- A _state_ in this context refers to a state machine state. The creation of a parse table is a long process that requires creating state machines. Check out [this slide deck](https://cons.mit.edu/sp13/slides/S13-lecture-03.pdf) from MIT 6.035 to learn more about this process.

Long story short, even a parse table of a very small grammar is pretty large. Constructing it for JSON grammar is a big task. So, we will try to implement the shift-reduce algorithm without any parse table.

The rest of the article will be divided into the following chapters:

- [Grammar](#grammar)
- [Lexer](#lexer)
- Parser

## Grammar

We have already seen a glimpse of the JSON grammar. In this section, we will provide the complete grammar. 

Let's start with some basic building blocks.

```go
type elementType = string

const (
	number   elementType = "<number>"
	integer  elementType = "<integer>"
	value    elementType = "<value>"
	array    elementType = "<array>"
	members  elementType = "<object fields>"
	member   elementType = "<object field>"
	element  elementType = "<array element>"
	elements elementType = "<array elements>"
	object   elementType = "<object>"
	boolean  elementType = "<boolean>"
	exponent elementType = "<exponent>"
	fraction elementType = "<fraction>"
	/* the rest represents literal tokens */
	ltObjectStart    elementType = "{"
	ltObjectEnd      elementType = "}"
	ltArrayStart     elementType = "["
	ltArrayEnd       elementType = "]"
	ltComma          elementType = ","
	ltColon          elementType = ":"
	ltFractionSymbol elementType = "."
	ltBoolean        elementType = "<bool_literal>"
	ltExponent       elementType = "e/E"
	ltDigits         elementType = "[0-9] (digits)"
	ltNull           elementType = "<null>"
	ltSign           elementType = "+/-"
	ltString         elementType = "<string_literal>"
)
```

- The following are the types of elements we will encounter while parsing the input JSON
- If you recall the Backus-Naur form we introduced earlier, there were the concepts of a terminal and non-terminal tokens.
- In above code snippet, constants prefixed with `lt` (meaning literal) are terminal tokens, while the rest are non-terminals.

Next is the structure that represents a grammar rule:

```go
type grammarRule struct {
	lhs    string
	rhs    [][]elementType
}
```
- It's pretty simple, a rule consists of a left-hand side (lhs) and the right-hand side (rhs).

```go
var grammar = []grammarRule{
	{value, [][]elementType{
		{object},
		{array},
		{number},
		{boolean},
		{ltString},
		{ltNull},
	}},
	{boolean, [][]elementType{
		{ltBoolean},
	}},
	{object, [][]elementType{
		{ltObjectStart, ltObjectEnd},
		{ltObjectStart, members, ltObjectEnd},
	}},
	{members, [][]elementType{
		{member},
		{members, ltComma, member},
	}},
	{member, [][]elementType{
		{ltString, ltColon, value},
	}},
	{array, [][]elementType{
		{ltArrayStart, ltArrayEnd},
		{ltArrayStart, elements, ltArrayEnd},
	}},
	{elements, [][]elementType{
		{element},
		{elements, ltComma, element},
	}},
	{element, [][]elementType{
		{value},
	}},
	{number, [][]elementType{
		{integer, fraction, exponent},
		{integer, fraction},
		{integer, exponent},
		{integer},
	}},
	{integer, [][]elementType{
		{ltDigits},
		{ltSign, ltDigits},
	}},
	{fraction, [][]elementType{
		{ltFractionSymbol, ltDigits},
	}},
	{exponent, [][]elementType{
		{ltExponent, integer},
	}},
}
```

- Let's take the rule `integer`. It means that it's either a string of digits or a string of digits prefixed with a sign.

## Lexer

Lexical analysis (or lexing, tokenization) is a process where we take a string input and try to tokenize it. A _token_ is still a string but with a meaning attached to it, such as an identifier, a right or left parenthesis, keyword, etc. In the case of lexing JSON, our token types will be the following:

- `ltObjectStart`
- `ltObjectEnd`
- `ltArrayStart`
- `ltArrayEnd`
- `ltComma`
- `ltColon`
- `ltFractionSymbol`
- `ltBoolean`
- `ltExponent`
- `ltDigits`
- `ltNull`
- `ltSign`
- `ltString`

When parsing JSON with the recursive descent, we do not need to tokenize the input, but tokenization makes things a bit easier for us when it comes to shift-reduce parsing.

Let's take a look at how lexing is done.

```go
type token struct {
	value     any
	tokenType elementType
}
```

- `tokenType` is any of the token types shown above
- `value` is the value of the token. For example, `{value:"1234", tokenType:ltDigits}`

```go
func lex(input string) ([]token, *Error) {
	var tokens []token
	for i := 0; i < len(input); {
		ch := input[i] // 1

		if _, ok := specialSymbols[ch]; ok { // 2
			tokens = append(tokens, token{
				tokenType: specialSymbols[ch],
			})
			i++
		} else if ch == '"' { // 3
			token, offset, err := lexString(input, i)
			if err != nil {
				return nil, err
			}
			tokens = append(tokens, token)
			i += offset
		} else if ch == 't' { // 4
			if "true" == input[i:i+4] {
				tokens = append(tokens, token{
					value:     "true",
					tokenType: ltBoolean,
				})
				i += 4
			} else {
				return nil, newError(i, "unrecognized token")
			}
		} else if ch == 'f' { // 5
			if "false" == input[i:i+5] {
				tokens = append(tokens, token{
					value:     "false",
					tokenType: ltBoolean,
				})
				i += 5
			} else {
				return nil, newError(i, "unrecognized token")
			}
		} else if ch == 'n' { // 6
			if "null" == input[i:i+4] {
				tokens = append(tokens, token{
					tokenType: ltNull,
				})
				i += 4
			} else {
				return nil, newError(i, "unrecognized token")
			}
		} else if isWhitespace(ch) {
			for i < len(input) && isWhitespace(input[i]) {
				i++
			}
		} else if ch == 'e' || ch == 'E' {
			tokens = append(tokens, token{
				tokenType: ltExponent,
			})
			i++
		} else if ch == '+' || ch == '-' {
			tokens = append(tokens, token{
				value:     ch,
				tokenType: ltSign,
			})
			i++
		} else if isDigit(ch) {
			token, offset := lexDigits(input, i)
			tokens = append(tokens, token)
			i += offset
		} else {
			return nil, newError(i, "unrecognized token")
		}
	}
	return tokens, nil
}
```

1. Take each character of the input string, try to match it to a condition and lex accordingly
2. `specialSymbols` is just a map of the symbols `{}[],:.` where the symbol maps to the token type.
3. If we encounter a double quotes, it means a string has started. The `lexString` function simply scans the input string from the position `i` until it sees another double quote. If it does not, it will return an error. `offset` is added to the index because we're done lexing until `i+offset` position.
4. If we encounter the char `t`, we check if it is the start of `true`
5. If we encounter the char `f`, we check if it is the start of `false`
6. If we encounter the char `n`, we check if it is the start of `null`
7. The rest of it is following the same logic. If we cannot find any match, that's an error.

## Parsing

[WIP]