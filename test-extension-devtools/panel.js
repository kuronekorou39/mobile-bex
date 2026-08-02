const output = document.getElementById("output");
const evalOutput = document.getElementById("eval-output");

// DevTools パネルからは tabs.query ではなく inspectedWindow を使う
// （パネルの対象は「アクティブなタブ」ではなく「検査中のタブ」）
function evalInInspectedWindow(expression) {
  return new Promise((resolve) => {
    chrome.devtools.inspectedWindow.eval(expression, (result, exceptionInfo) => {
      if (exceptionInfo) {
        resolve({
          error:
            exceptionInfo.description ||
            exceptionInfo.value ||
            "eval failed"
        });
      } else {
        resolve({ result });
      }
    });
  });
}

// Show inspected page info
document.getElementById("inspect-btn").addEventListener("click", async () => {
  const { result, error } = await evalInInspectedWindow(
    "({ url: location.href, title: document.title, charset: document.characterSet })"
  );
  if (error) {
    output.textContent = "Error: " + error;
  } else {
    output.textContent = ["tabId: " + chrome.devtools.inspectedWindow.tabId]
      .concat(Object.entries(result).map(([k, v]) => k + ": " + v))
      .join("\n");
  }
});

// Eval document.title
document.getElementById("eval-btn").addEventListener("click", async () => {
  const { result, error } = await evalInInspectedWindow("document.title");
  evalOutput.textContent = error ? "Error: " + error : '"' + result + '"';
});
