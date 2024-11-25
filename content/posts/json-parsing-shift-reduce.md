<!--
title=How to parse JSON using shift-reduce parsing approach
date=2023-11-09T01:12:33-06:00
draft=false
-->

Parsing JSON is something that the majority of programmers have done. Almost all languages have means to deserialize (unmarshall) JSON from text into some data structure. In this article, we are going to try doing exactly that.

### Grammar

Just like in natural languages, the programming languages and various data formats have a grammar. The grammar consists of rules that show how the text input needs to be structured. For JSON the following is a simplified version of a part of the grammar:

```text
1. json ::= value
2. value ::= object | array | string
3. object ::= '{' members '}'
4. members ::= member | member ',' members
5. member ::= string ':' value
6. string ::= '"' characters '"'
```

Check out the full grammar [here](https://www.crockford.com/mckeeman.html), but we will also go over the grammar later. The format shown above is called the BNF or [Backus-Naur form](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form). Most programming languages have a BNF grammar. Each line in the grammar above is called a _production rule_. Anything that's in single quotes above is called a _terminal_ symbol. Terminal means that we can no longer expand that part of the rule to something else. For example, if we take a look at the "object" rule above, the opening and closing braces are terminals which mean those exact characters need to be present for any piece of text to be even considered as JSON object. The remaining ones are called _non-terminals_. Non-terminals get expanded into their constituent parts. The following is just a simplified example of an expansion to match `{"name": "jane"}`:

```go
value ::= object
 // object -> '{' members '}'
value ::= '{' members '}'
// members -> member
value ::= '{' member '}' 
// member -> string ':' value
value ::= '{' string ':' value '}' 
// value -> string
value ::= '{' string ':' string '}' 
// string -> '"' characters '"'
value ::= '{' '"' characters '"' ':' string '}' 
// characters -> "name"
value ::= '{' '"' name '"' ':' string '}' 
// string -> '"' characters '"'
value ::= '{' '"' name '"' ':' '"' characters '"' '}'
// characters -> "jane" 
value ::= '{' '"' name '"' ':' '"' jane '"' '}'
```

Parsing is the process of taking a text input and producing some sort of a data structure (oftentimes a tree). There are different ways of parsing. One of which is called _recursive descent_ or _top-down parsing_. In this type of parsing, we start from the first character of the input and recursively apply different production rules (like we did above) to create a tree structure. So, let's take a look at a simple example.

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

The most obvious feature of recusive descent is the fact that the code actually resembles the grammar. It is used to parse JSON in golang's [standard library](https://github.com/golang/go/blob/e73e25b624c37a936bb42f50a11f56297a4cd637/src/encoding/json/encode.go#L159). I've also written a [top-down JSON parser](https://github.com/rhaeguard/jsonx/blob/45919f19218139c233fbdf57cb1213a03d5a6f78/src/main/java/io/rhaeguard/JsonX.java). 

Recursive descent/top-down parsing is awesome, but there are other ways of parsing as well. Bottom-up parsing is another approach that's extremely common. Especially with parser generators like [yacc](https://en.wikipedia.org/wiki/Yacc). As the name implies, in bottom-up parsing, we go from ground up. What this means is that we try to construct the parts of the parse tree that we know, and slowly grow the parse tree. For the example above, this could mean that we can construct a _string_ first, and based on those, we can recognize that we have a _member_, and then create _members_ and _object_ and finally end up with the root _json_. 

You can also check out Professor Brailsford's video on Computerphile on this subject as he explains stuff way better than I can.

<iframe width="100%" height="315" src="https://www.youtube.com/embed/tH5AOX9929g?si=PRfAEyXSmLUT-37m" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

In this tutorial, we will use a bottom-up approach, namely shift-reduce, to parse JSON. We will use Golang, but the concepts can be coded in any language.

# Shift-Reduce Parsing

The shift-reduce parsing approach is a table-driven parsing approach that consists of 2 operations - shift and reduce. Here's the simplified version of the algorithm:

```text
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

- `rn` is reducing to the rule number `n`
- `sn` is shifting the lookahead and moving to state `n`
- `acc` indicates successful parsing
- goto column indicates which state to move into
- A _state_ in this context refers to a state machine state. The creation of a parse table is a long process that requires creating state machines. Check out [this slide deck](https://cons.mit.edu/sp13/slides/S13-lecture-03.pdf) from MIT 6.035 to learn more about this process.

Long story short, even a parse table of a very small grammar is pretty large. Constructing it for JSON grammar is a big task. So, we will try to implement the shift-reduce algorithm without any parse table.

The rest of the article will be divided into the following chapters:

- [Grammar](#grammar)
- [Lexer](#lexer)
- [Parser](#lexer)

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
- If you recall the Backus-Naur form we introduced earlier, there were the concepts of terminal and non-terminal tokens.
- In above code snippet, constants prefixed with `lt` (meaning literal) are terminal tokens, while the rest are non-terminals.

Next is the structure that represents a grammar rule:

```go
type grammarRule struct {
	lhs    string
	rhs    [][]elementType
}
```
- It's pretty simple, a rule consists of a left-hand side (lhs) and the right-hand side (rhs).

And the following is the grammar:

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
- `number` is simply a combination of an integer, a fraction and an exponent where the fraction and the exponent could be omitted.

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

Let's take a look at how lexing is done. This is the token structure that will hold the each lexed value.

```go
type token struct {
	value     any
	tokenType elementType
}
```

- `value` is the value of the token. For example, `{value:"1234", tokenType:ltDigits}`
- `tokenType` is any of the token types shown above

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

This is an example of what the lexer produces for the string: `{"hello": 12345}`

```go
[
	{<nil> { } // object start
	{hello <string_literal> } // hello string
	{<nil> : } // colon
	{12345 [0-9] (digits) } // the digits 
	{<nil> } } // object end
]
```

## Parsing

As we already know the shift-reduce parsing approach has (at least) two operations: shift and reduce. 

Shifting a token simply means pushing that token to the top of the parse stack. In our tableless approach, we will only shift in the following cases:
- If lookahead is a prefix of the right hand side of any rule.
- If a combination of top stack elements and the lookahead is a prefix of the right hand side of any rule.

There's a case, however, in which the combination might have a complete match, not just prefix:
- If the full match is the only match, we still shift, but we have to reduce afterwards
- If there are potentially longer matches than the full match, we only shift as shown above

Reducing operates on the elements at the top of the stacks. If the elements line up in a certain way that match the right hand side of a rule completely, then those elements are popped off the stack and replaced with the left-hand side of that rule.

In shift-reduce, we try to maximize the amount of elements we reduce in one iteration. This is the reason why we will shift the tokens if there's a prefix match which simply means that we can potentially reduce a longer rule. If we just cannot find any match, we do not shift, we try to reduce first, and then try with the same token to see if it matches with anything, given a reduce is performed. Finally, if we cannot perform neither shift nor reduce, that's an error.

Let's actually see this in action before we introduce the code. Let's take the grammar we saw earlier.

1. E → E * B
2. E → E + B
3. E → B
4. B → 0
5. B → 1

and let's parse `1+1` with it

<table>
	<thead>
		<tr>
			<th>parse stack</th>
			<th>lookahead</th>
			<th>unparsed tokens</th>
			<th>explanation</th>
		</tr>
	</thead>
		<tr>
			<td>[]</td>
			<td>1</td>
			<td>+ 1</td>
			<td>nothing parsed yet, lookahead is 1</td>
		</tr>
		<tr>
			<td>[1]</td>
			<td></td>
			<td>+ 1</td>
			<td>1 completely matches with rule 5, so we shift and we'll reduce next</td>
		</tr>
		<tr>
			<td>[B]</td>
			<td></td>
			<td>+ 1</td>
			<td>reduce 1 -> B by following rule 5</td>
		</tr>
		<tr>
			<td>[B]</td>
			<td>+</td>
			<td>1</td>
			<td>
				neither +, nor B+ is a prefix of anything - no shifting</br>
				reduce B -> E by rule 3
			</td>
		</tr>
		<tr>
			<td>[E]</td>
			<td>+</td>
			<td>1</td>
			<td>E+ is prefix of rule 2, so we shift</td>
		</tr>
		<tr>
			<td>[E+]</td>
			<td>1</td>
			<td></td>
			<td>1 completely matches with rule 5, so we shift and we'll reduce next</td>
		</tr>
		<tr>
			<td>[E+1]</td>
			<td></td>
			<td></td>
			<td>reduce 1 -> B by rule 5</td>
		</tr>
		<tr>
			<td>[E+B]</td>
			<td></td>
			<td></td>
			<td>reduce E+B -> E by rule 2</td>
		</tr>
		<tr>
			<td>[E]</td>
			<td></td>
			<td></td>
			<td>done</td>
		</tr>
	<tbody></tbody>
</table>

Now that we've seen an example of how shift-reduce works, let's take a look at the code. But before that, we have a couple of useful structs and constants:

```go
type stackElement struct {
	value token
	rule  *jsonElement
}

type jsonElement struct {
	value           interface{}
	jsonElementType elementType
}

const (
	STRING JsonValueType = "STRING"
	NUMBER JsonValueType = "NUMBER"
	BOOL   JsonValueType = "BOOLEAN"
	NULL   JsonValueType = "NULL"
	OBJECT JsonValueType = "OBJECT"
	ARRAY  JsonValueType = "ARRAY"
)

type JsonValue struct {
	Value     interface{}
	ValueType JsonValueType
}
```

- `stackElement` holds the elements of the parse stack, it can hold either a literal token (_terminal_), or the left-hand side of the rule (_non-terminal_)
- `jsonElement` represents a non-terminal. It can be an integer, for example, and its value would be the digits of an integer.
- The constants are all the potential types of values a JSON can have
- `JsonValue` is a struct that simply holds a particular JSON value. It can be a number, it can be a boolean, or it can be another `JsonValue` that holds a number or an object. You get the idea.

Now, finally the code (_some currently irrelevant parts have been omitted for clarity_):

```go
func Parse(input string) (JsonValue, *Error) {
	tokens, err := lex(input) // 1

	// err check (omitted)

	var stack []*stackElement // 2

	size := len(tokens)
	reducePerformed := true // 3

	for i := 0; i < size; {
		lookahead := tokens[i] // 4

		// 5
		if matchType := checkIfAnyPrefixExists(stack, lookahead); matchType != noMatch {
			i++
			// 5-1
			stack = append(stack, &stackElement{value: lookahead})

			if matchType == partialMatch { // 5-2
				continue
			}
			// 5-3
			// full match means that there's something we can reduce now
		} else if !reducePerformed { // 6
			// return err (omitted)
		}

		// 7
		if jsonElement, offset := action(stack); offset != 0 {
			stack = stack[:len(stack)-offset] // 7-1
			stack = append(stack, &stackElement{ // 7-2
				rule: jsonElement,
			})
			reducePerformed = true // 7-3
		} else {
			reducePerformed = false
		}
	}

	// 8
	for {
		if jsonElement, offset := action(stack); offset != 0 {
			stack = stack[:len(stack)-offset] 
			stack = append(stack, &stackElement{
				rule: jsonElement,
			})
		} else {
			break
		}
	}

	// 9-1
	if len(stack) != 1 {
		return JsonValue{}, newError(-1, "parsing failed...")
	}

	// 9-2
	values := stack[0].rule.value.(JsonValue).Value.([]JsonValue)
	if len(values) != 1 {
		return JsonValue{}, newError(-1, "parsing failed...")
	}

	return values[0], nil
}
```
1. Lexing gives us the tokens to parse. `tokens` is simply an array of tokens
2. `stack` is the parse stack
3. `reducePerformed` keeps track of whether a reduce was performed in the previous iteration of the loop or not. Because if we cannot shift and reduce, then that's an error.
4. We get the current lookahead. Lookahead is simply a `token`
5. We will examine `checkIfAnyPrefixExists` function soon, but for now all we need to know is that it returns a value that's one of: `noMatch, partialMatch, fullMatch`
	1. In any match condition, we push the value to the stack
	2. If it's a `partialMatch`, however, we do not reduce, we move on to the next token, because there's a chance for reducing a longer rule.
	3. If it's a `fullMatch`, we move on to reducing
6. If we couldn't shift anything and we didn't reduce in the previous step, that's an error.
7. We will examine `action` function soon, but for now all we need to know is that it performs the reductions if there are any. `offset` is the number of elements we need to remove off the top of the stack. If it is `0`, it simply means no reduction was possible. 
	1. We remove the necessary number of elements from the parse stack.
	2. We push the new element to the stack.
	3. We set the flag to true to indicate that a reduction was performed.
8. Once we exhaust all the tokens, we try to repeatedly apply reduction until it is not possible. 
9. At the end of the parsing, our stack should only contain one element. This is because our JSON grammar can be reduced to a single rule.
	1. Checking to see if we have indeed one element in the parse stack.
	2. This line looks complicated, and a lot of casting is going on. To completely understand what's going on, we need to know what `toJson` function does which hasn't been introduced yet. So, it'd be a better idea to come back here once you read the corresponding section. Here's what happens:
		- In the case of successful parsing, no matter if we have an object, array, boolean, etc., these are reduced to `value` rule.
		- However, if we take a look at the grammar. We see that the `value` itself is a part of `element` which itself is a part of `elements`. So, at the end, the actual parsed value is inside the JSON array. That's why we need these long casts.
		- `stack[0].rule.value.(JsonValue)` takes the only element of the stack, extracts the value and casts it to `JsonValue` because the field we used to store values in our parse stack is generic.
		- The type of this new parsed object is `ARRAY` and it's `Value` is a `[]JsonValue`. So, `.Value.([]JsonValue)` this gives us the whole array
		- Then, after the size check to make sure we have indeed 1 element, we extract that one parsed JSON value.


Let's start talking about the functions we glossed over first, namely, `checkIfAnyPrefixExists` and `action`.

```go
func checkIfAnyPrefixExists(stack []*stackElement, lookahead token) prefixMatch {
	var elems []elementType // 1

	stackSize := len(stack)
	if stackSize >= 2 { // 2
		elems = append(elems, stackToToken(stack[stackSize-2:])...)
	} else if stackSize == 1 { // 3
		elems = append(elems, stackToToken(stack[0:1])...)
	}

	elems = append(elems, lookahead.tokenType) // 4

	size := len(elems)
	for i := size - 1; i >= 0; i-- { // 5
		// 6
		if matchType := checkPrefix(elems[i:size]...); matchType != noMatch {
			return matchType
		}
	}

	return noMatch // 7
}
```
0. The basic idea is that we want to try out different combinations of the top 2 stack elements and the lookahead to see if they match with any rule. The reason why the max combination length is 3 (2 stack elements + 1 lookahead) is because that's the max length of the right hand side expansion of any rule in our JSON grammar.
1. `elems` holds all the elements from the stack
2. If stack has more than 2 elements, we can simply pick the last 2
3. If stack has exactly 1 element, we simply pick that element
4. Finally we also add the lookahead to the mix
5. We check the combinations in the following way:
	1. Assume `elems` is `[s1 s2 la]`
	2. We wil check `[la]` first
	3. We will check `[s2 la]` next
	4. We will finally check `[s1 s2 la]`
6. If there's any match, we will return the type of that match.
7. If no match is found, we return `noMatch`

We will skip over `stackToToken` and `checkPrefix` functions, but you're welcome to check them out on the Github repository.

Let's move on to the `action` function.

```go
func action(stack []*stackElement) (*jsonElement, int) {
	stackSize := len(stack)

	// 1
	var je *jsonElement
	var offset int

	for _, rule := range grammar { // 2
		for _, production := range rule.rhs { // 3
			size := len(production)
			if size > stackSize { // 4
				continue
			}
			actual := topNOfStack(stack, size) // 5
			matches := compare(production, actual) // 6
			if matches && size > offset { // 7
				je = &jsonElement{
					// 8
					value:           rule.toJson(stack[len(stack)-size:]...),
					// 9
					jsonElementType: rule.lhs,
				}
				offset = size // 10
			}
		}
	}

	return je, offset // 11
}
```

1. These are the values we will set and return
2. Go over each rule in the grammar
3. Go over each production of each rule
4. If the production is longer than the stack itself, skip that rule
5. Take the required number of elements off the top of the stack.
6. Compare the actual stack elements with the production elements
7. If there's a match, and the rule is bigger than the previously matched rule, set the values
8. `toJson` is a new field added to the `grammarRule` struct which simply creates a `JsonValue` for us, otherwise we would simply lose the parsed value. We'll take a look at how it works in a bit.
9. The type of the `jsonElement` is the left-hand side of the rule. This means that if the matching combination was: `[ltSign, ltDigit]`, the `jsonElementType` will be `integer` (_this rule exists in the grammar shared above_).
10. Update the offset to the new, bigger size.
11. Return the values.

After putting together all the functions we've described, we are going to be able to create a parse tree, but we will not be able to preserve the actual values of the JSON. We need to keep track of the actual values while building up the tree. That's where `toJson` function comes in. Let's start by checking the signature:

```go
type grammarRule struct {
	lhs    string
	rhs    [][]elementType
	toJson func(values ...*stackElement) JsonValue
}
```
- It will take some stack elements. These elements will be the ones that have matched in the `action` step (refer to #8 in `action` function above).
- Given those matched elements, it will try constructing the appropriate `JsonValue`.
- Each grammar entry will have a different strategy for generating the `JsonValue`.

Let's take a look at an example:

```go
grammarRule{integer, [][]elementType{
	{ltDigits},
	{ltSign, ltDigits},
}, func(values ...*stackElement) JsonValue {
	size := len(values)
	digits := values[size-1] // 1
	var sign uint8 = '+' // 2
	if size == 2 { // 3
		sign = values[0].Value().(uint8) // - or +
	}
	v := fmt.Sprintf("%c%s", sign, digits.Value()) // 4
	// 5
	return JsonValue{
		Value:     v,
		ValueType: NUMBER,
	}
}},
```
1. The `integer` rule has two productions. The last element of both productions is the digits. 
2. An integer might have a sign, so the default value for sign is `+`.
3. If `values` has two elements, it means we have found a match for the second production rule: `{ltSign, ltDigits}`, so we will try to extract the value of that stack entry.
4. We create the integer string. We will have values such as `+2` or `-10`
5. Return the created `JsonValue`

`integer` is a part of a bigger rule which is `number`. `number` has two more components which are `fraction` and `exponent`. Let's take a look at each and finally how they are all put together.

```go
grammarRule{fraction, [][]elementType{
	{ltFractionSymbol, ltDigits},
}, func(values ...*stackElement) JsonValue {
	// 1
	var fractionDigits = fmt.Sprintf(".%s", values[1].Value())

	return JsonValue{
		Value:     fractionDigits,
		ValueType: NUMBER,
	}
}},

grammarRule{exponent, [][]elementType{
	{ltExponent, integer},
}, func(values ...*stackElement) JsonValue {
	// 2
	var exponentExpr = fmt.Sprintf("e%s", values[1].asJsonValue().Value.(string))

	return JsonValue{
		Value:     exponentExpr,
		ValueType: NUMBER,
	}
}},
```
0. The code for both `fraction` and `exponent` are almost the same. So, let's take a look at the difference.
1. For `fraction`, the most important part is the `digits`, because the fraction symbol is always `.` anyway. So, we simply take the digits value, make it a string and return.
2. For `exponent`, the most important part is the `integer`. We saw earlier what `integer` returned. The `Value` of an `integer` is a string, so we simply cast the last element to `JsonValue` (`asJsonValue` is just a helper method), and grab the string value.

Now that we have all the constituents of the `number` rule. Let's see how it's all put together. It's simpler than it looks:

```go
grammarRule{number, [][]elementType{
	{integer, fraction, exponent},
	{integer, fraction},
	{integer, exponent},
	{integer},
}, func(values ...*stackElement) JsonValue {
	size := len(values)
	// 1
	var integerValue = values[0].asJsonValue().Value.(string)

	// 2
	var fraction string
	if size >= 2 && strings.HasPrefix(values[1].asJsonValue().Value.(string), ".") {
		fraction = values[1].asJsonValue().Value.(string)
	} else {
		fraction = ""
	}

	// 3
	var exponent string
	if size == 2 && strings.HasPrefix(values[1].asJsonValue().Value.(string), "e") {
		exponent = values[1].asJsonValue().Value.(string)
	} else if size == 3 && strings.HasPrefix(values[2].asJsonValue().Value.(string), "e") {
		exponent = values[2].asJsonValue().Value.(string)
	} else {
		exponent = ""
	}
	
	// 4
	expression := fmt.Sprintf("%s%s%s", integerValue, fraction, exponent)
	// 5
	value, err := strconv.ParseFloat(expression, 64) // TODO: potential for an error!

	if err != nil {
		fmt.Printf("%s\n", err.Error())
	}

	// 6
	return JsonValue{
		Value:     value,
		ValueType: NUMBER,
	}
}},
```
1. From the production rules, we know that the first element is always `integer`. So, we grab the value as string
2. `fraction` may or or may not be the second element. So, if it is, we save the value to the `fraction` variable.
3. `exponent` can be the second or the third element, or non-existent. So, based on these cases, we try to grab the string value and save it to `exponent` variable
4. The format for the final expression is: `<integer><fraction><exponent>`. Keep in mind that `fraction` and `exponent` can be empty.
5. With the help of golang's `strconv.ParseFloat` method, we parse the expression to a numeric value. All the numeric values will be in `float64` type.
6. Return the number.

There are a lot more `toJson` implementations that we did not cover, but the logic is the same across all. Take the passed `values` argument and based on the known grammar rules, try to create the target `JsonValue` object. Feel free to check out the Github repository for the full implementation.

That's technically it! We now have a working shift-reduce parser. Let's take a look at a test to get a better understanding of the input and the output.

```go
func TestParse(t *testing.T) {
	var inputJson = `{
    "value": [
        1239,
        123.45
    ],
    "name": "renault",
    "token": true,
    "hello": null
}`
	t.Run("check json", func(t *testing.T) {
		json, err := Parse(inputJson)
		if err != nil {
			t.Fatalf("%s", err.Error())
		}
		expected := JsonValue{
			ValueType: OBJECT,
			Value: map[string]JsonValue{
				"value": {
					ValueType: ARRAY,
					Value: []JsonValue{
						{ValueType: NUMBER, Value: float64(1239)},
						{ValueType: NUMBER, Value: float64(123.45)},
					},
				},
				"name": {
					ValueType: STRING,
					Value:     "renault",
				},
				"token": {
					ValueType: BOOL,
					Value:     true,
				},
				"hello": {
					ValueType: NULL,
					Value:     nil,
				},
			},
		}

		if !reflect.DeepEqual(json, expected) {
			t.Fail()
		}
	})
}
```

## Unmarshalling

We have already achieved our goal, but more often than not, people want to deserialize their JSON payload into a custom struct or a custom object. In this section, we will make use of Golang's [reflect](https://pkg.go.dev/reflect) package to achive this. This section is going to be code-heavy.

```go
// Unmarshal deserializes the parsed JsonValue into the provided object.
// Please keep in mind that obj needs to be a pointer
// to the object we want to deserialize the json into
func (jv *JsonValue) Unmarshal(ptr any) error {
	v := reflect.ValueOf(ptr) // 1

	if v.Kind() != reflect.Pointer { // 2
		return errors.New("expected: a pointer")
	}

	kind := v.Elem().Kind() // 3

	if _, ok := isSupported(kind); !ok { // 4
		return errors.New(fmt.Sprintf("unsupported type: %s", kind.String()))
	}

	return jv.setValue(kind, v.Elem()) // 5
}
```
0. `Unmarshal` is a function that takes a `JsonValue` object and a pointer to a supposedly valid type.
1. We get the value of this provided object
2. If it is not a pointer, we return an error
3. If it's a pointer, we extract the type it's pointing to
4. If that type is not supported, we return an error
	- `isSupported` is simply a function that checks if the `kind` is a string, boolean, number, slice, etc.
5. Once we pass all the checks, it's time to set the value.

```go
type numberConverter = func(i float64) interface{}

var numbers = map[reflect.Kind]numberConverter{
	reflect.Int: func(i float64) interface{} {
		return int(i)
	},
	reflect.Int8: func(i float64) interface{} {
		return int8(i)
	},
	reflect.Int16: func(i float64) interface{} {
		return int16(i)
	},
	// most of the converters are omitted
}

func (jv *JsonValue) setValue(kind reflect.Kind, v reflect.Value) error {
	jt, _ := isSupported(kind) 
	if jt != jv.ValueType { // 1
		return errors.New(fmt.Sprintf("type mismatch: expected: %s, provided: %s", jv.ValueType, jt))
	}

	if kind == reflect.String { // 2
		v.Set(reflect.ValueOf(jv.Value))
	} else if kind == reflect.Bool { // 3
		v.Set(reflect.ValueOf(jv.Value))
	} else if converter, ok := numbers[kind]; ok { // 4
		v.Set(reflect.ValueOf(converter(jv.Value.(float64))))
	} else if kind == reflect.Slice { // 5
		if err := jv.handleSlice(v, jt, ok); err != nil {
			return err
		}
	} else if kind == reflect.Struct { // 6
		m := jv.Value.(map[string]JsonValue) // 6-1

		for k, val := range m {
			f := v.FieldByName(k) // 6-2
			if err := val.setValue(f.Kind(), f); err != nil { // 6-3
				return err
			}
		}

	}
	return nil // 7
}
```

1. If the type of the provided pointer does not match with what the JSON object contains, then that's a mismatch
2. If the kind is string, we simply set the value to that object (`jv.Value` is already a string)
3. If the kind is boolean, we simply set the value to that object (`jv.Value` is already a boolean)
4. If the kind is a number, we have to find the correct converter for that number. The provided pointer can have a type of `uint`, `int32`, `float32` etc. `number` map contains these converters
5. If the kind is a slice, we handle it in a separate function that'll be covered next
6. if the kind is a struct
	1. We cast the value of the JSON object to a map of string to `JsonValue` entries
	2. For each entry in the map, we try to get the field with the same name from the struct. So, if our JSON contains `Name` field, we will look for a `Name` field in the struct as well. Please keep in mind that in Golang, capitalized names indicate public accessibility. `FieldByName` simply cannot find the field if it's lowercase. Thus we have the restriction of making our JSON fields capitalized. This issue can be tackled in several ways, such as simply introducing a field name mapper, but it's out of scope for this tutorial.
	3. Since value of the map entry is a `JsonValue`, we can call the `setValue` function recursively. If any error occurs, we return it
7. If no error occurs, we return `nil` indicating success

Let's now take a look at `handleSlice`:

```go
func (jv *JsonValue) handleSlice(v reflect.Value, jt JsonValueType) error {
	dataType := v.Type().Elem().Kind() // 1

	values := jv.Value.([]JsonValue) // 2
	var jsonType = values[0].ValueType // 3

	for _, value := range values { // 4
		if value.ValueType != jsonType { // 4-1
			return errors.New("json array does not have elements of one type")
		}
	}

	// 5
	if jt, ok := isSupported(dataType); !ok || jt != jsonType {
		return errors.New("type mismatch for array")
	}

	// 6
	refSlice := reflect.MakeSlice(reflect.SliceOf(v.Type().Elem()), len(values), len(values))

	// 7
	for i := 0; i < len(values); i++ {
		// 7-1
		if err := values[i].setValue(dataType, refSlice.Index(i)); err != nil {
			return err
		}
	}
	// 8
	v.Set(refSlice)
	// 9
	return nil
}
```

1. We get the data type of the user-provided slice
2. We cast the JSON value to a slice of `JsonValue`
3. We get the actual type of the parsed JSON array
4. We make sure that types of all the array entries match
	1. If they do not, we return an error
5. If the sliec data type is not actually supported or the type of the slice and the type of the actual JSON array mismatch, we return an error
6. We create a slice of the required size and of required type
7. We go through each value in the JSON array
	1. We try to set the value for each entry, one by one. If we encounter an error, we return the error
8. `refSlice` is a slice we created inside the function, it's not the actual reference passed by the user, so we need to set user provided pointer to the slice we created.
9. Return `nil` because no error occurred.

Here's a test showing how it's actually used:

```go
type Person struct {
	Name string
	Age  uint8
}

type ComplexPerson struct {
	Person       Person
	Job          string
	LuckyNumbers []int
}

func TestUnmarshalling(t *testing.T) {
	input := `{
		"Person": {
			"Name": "John", 
			"Age": 25
         }, 
 		"Job": "Plumber", 
		"LuckyNumbers": [-1, 0, 1, 1022]
	}`

	var cPerson ComplexPerson

	expected := ComplexPerson{
		Person:       Person{Name: "John", Age: 25},
		Job:          "Plumber",
		LuckyNumbers: []int{-1, 0, 1, 1022},
	}

	t.Run("test", func(t *testing.T) {
		json, _ := Parse(input)
		_ = json.Unmarshal(&cPerson)
		if !reflect.DeepEqual(cPerson, expected) {
			t.Fatalf("expected: '%-v'", expected)
		}
	})
}
```

That's it! You can find the full implementation in the [Github repository](https://github.com/rhaeguard/gojson). 

Cheers!

# References

- My code is mostly based on these videos from Shawn Lupoli:
  - https://www.youtube.com/watch?v=3XLT1AI1f0g
  - https://www.youtube.com/watch?v=RGGVlzO4vD0
- To learn more about parse trees:
  - https://cons.mit.edu/sp13/slides/S13-lecture-03.pdf
  - https://www.youtube.com/watch?v=8Cq3EIgXOec
- General useful information:
  - https://www.cs.binghamton.edu/~zdu/parsdemo/srintro.html
  - https://en.wikipedia.org/wiki/Shift-reduce_parser
  - https://www.youtube.com/watch?v=1_qjmZXFaNw
  - https://github.com/aberamseyer/LR1/blob/master/README.md