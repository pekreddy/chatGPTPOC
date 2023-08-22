import { UserInfo, ConversationRequest, SummaryRequest} from "./models";

export async function conversationApi(options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {
    const response = await fetch("/conversation1", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            messages: options.messages
        }),
        signal: abortSignal
    });

    return response;
}

export async function summaryApi(text: string): Promise<Response> {
    const response = await fetch("/summarize", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: text,
    });

    return response;
}

export async function langSummaryApi(text: string):Promise<Response> {
    console.log("text",text)
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "text/plain");
    const response :any = await fetch("/langsummarize", {
        method: 'POST',
        headers: myHeaders,
        body: text,
        redirect: 'follow'
      })
        return response;
}

export async function getUserInfo(): Promise<UserInfo[]> {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
        console.log("No identity provider found. Access to chat will be blocked.")
        return [];
    }

    const payload = await response.json();
    return payload;
}