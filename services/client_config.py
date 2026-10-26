"""
Load client preferences and templates.
Configured with iMocha platform coding standards and authoring specifications.
"""

LANGUAGE_TIERS = {
    "T1": ["python", "javascript", "java", "cpp", "c", "csharp", "go"],
    "T2": ["typescript", "ruby", "php", "swift", "kotlin", "r"],
    "T3": ["sql", "html", "css", "react", "system_design"],
}

def get_language_tier(language: str) -> str:
    for tier, langs in LANGUAGE_TIERS.items():
        if language.lower() in langs:
            return tier
    return "T2"  # Unknown -> conservative default

DEV_CLIENT_CONFIG = {
    "question_style":   "imocha_standard",
    "difficulty_bias":  0.0,
    "html_template_id": "imocha_html_v1",
    "html_template": """<em><strong>{{title}}</strong></em><br />
<br />
{{scenario}}<br />
<br />
<em><strong>{{action_prompt}}</strong></em><br />
<br />
<!--[if--><strong><u>Function Description</u></strong><br />
In the provided code snippet, implement the provided <strong><code>{{function_name}}(...)</code></strong>method to find {{goal}}.&nbsp;You can write your code in the space below the phrase <code><strong>&ldquo;</strong><strong>WRITE YOUR LOGIC HERE</strong><strong>&rdquo;</strong></code>.<br />
<br />
There will be multiple test cases running, so the Input and Output should match exactly as provided.<br />
The base Output variable <code><strong>result</strong></code> is set to a default value <code><strong>-404</strong></code> which can be modified. Additionally, you can add or remove these output variables.<br />
<br />
<strong><u>Input Format</u></strong><br />
{{input_format}}<br />
<!--[if--><br />
<strong><u>Sample Input</u></strong><br />
<div style="background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;">{{sample_input_annotated}}</div>
<br />
<strong><u>Constraints</u></strong><br />
{{constraints}}<br />
<br />
<strong><u>Output Format</u></strong><br />
{{output_format}}<br />
<br />
<strong><u>Sample Output</u></strong><br />
<div style="background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;">{{sample_output}}</div>
&nbsp;<br />
<strong><u>Explanation</u></strong><br />
Given<br />
<ul>
{{explanation_bullets}}
</ul>
{{explanation_text}}<br />
<br />
Hence, the output is <em><strong>{{sample_output}}</strong></em>.<!--!--><!--[endif]--><!--[if--><!--[endif]--><!--!--><!--[if-->""",
    "code_template_id": "imocha_default",
    "code_template": {
        "c": """#include <stdio.h>

int {{function_name}}(int N, int K, int A[]){

    //this is default OUTPUT. You can change it.
    int result = -404;

    //write your Logic here:



    return result;
}

int main(){
    //INPUT [uncomment & modify if required]
    int N;
    scanf("%d", &N);

    int K;
    scanf("%d", &K);

    int A[N];
    for(int i = 0; i < N; i++){
        scanf("%d", &A[i]);
    }

    //OUTPUT [uncomment & modify if required]
    printf("%d", {{function_name}}(N, K, A));

    return 0;
}
""",
        "cpp": """#include <iostream>
using namespace std;

int {{function_name}}(int N, int K, int A[]){

    //this is default OUTPUT. You can change it.
    int result = -404;

    //write your Logic here:



    return result;
}

int main(){
    //INPUT [uncomment & modify if required]
    int N;
    cin >> N;

    int K;
    cin >> K;

    int A[N];
    for(int i = 0; i < N; i++){
        cin >> A[i];
    }

    //OUTPUT [uncomment & modify if required]
    cout << {{function_name}}(N, K, A);

    return 0;
}
""",
        "python": """import sys

def {{function_name}}(N: int, K: int, A: list[int]) -> int:
    # this is default OUTPUT. You can change it.
    result = -404

    # write your Logic here:



    return result

def main():
    lines = sys.stdin.read().split()
    if not lines:
        return
    N = int(lines[0])
    K = int(lines[1])
    A = [int(x) for x in lines[2:2 + N]]
    print({{function_name}}(N, K, A))

if __name__ == "__main__":
    main()
""",
        "javascript": """const fs = require('fs');

function {{function_name}}(N, K, A) {
    // this is default OUTPUT. You can change it.
    let result = -404;

    // write your Logic here:

    return result;
}

function main() {
    const input = fs.readFileSync('/dev/stdin', 'utf-8').trim().split(/\\s+/);
    if (!input || input.length < 2) return;
    const N = parseInt(input[0], 10);
    const K = parseInt(input[1], 10);
    const A = input.slice(2, 2 + N).map(x => parseInt(x, 10));
    console.log({{function_name}}(N, K, A));
}

main();
""",
        "java": """import java.util.*;

public class Solution {
    public static int {{function_name}}(int N, int K, int[] A) {
        // this is default OUTPUT. You can change it.
        int result = -404;

        // write your Logic here:

        return result;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNextInt()) return;
        int N = sc.nextInt();
        int K = sc.nextInt();
        int[] A = new int[N];
        for (int i = 0; i < N; i++) {
            A[i] = sc.nextInt();
        }
        System.out.println({{function_name}}(N, K, A));
    }
}
""",
    },
}


async def load_client_config(
    client_id:     str,
    language:      str,
    question_type: str = "ALGORITHMIC",
) -> dict:
    """
    Returns client preferences and language-specific authoring templates.
    """
    config          = dict(DEV_CLIENT_CONFIG)
    templates       = config.pop("code_template", {})
    lang_key        = language.lower()
    config["code_template"] = templates.get(lang_key, templates["python"])
    return config
