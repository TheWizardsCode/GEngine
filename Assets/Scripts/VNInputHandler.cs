using UnityEngine;
using UnityEngine.UI;

public class VNInputHandler : MonoBehaviour
{
    [TextArea]
    public string[] pages = new string[] { "Page 1", "Page 2", "Page 3" };

    public Text displayText;
    public Button nextButton;

    public int currentPage { get; private set; } = 0;

    void Awake()
    {
        if (displayText == null)
            Debug.LogWarning("VNInputHandler: displayText is not assigned");
        if (nextButton == null)
            Debug.LogWarning("VNInputHandler: nextButton is not assigned");

        if (nextButton != null)
            nextButton.onClick.AddListener(AdvancePage);
    }

    void Start()
    {
        Refresh();
    }

    void OnDestroy()
    {
        if (nextButton != null)
            nextButton.onClick.RemoveListener(AdvancePage);
    }

    void Update()
    {
        // Space or Enter advances page
        if (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.Return))
        {
            AdvancePage();
        }

        // Mouse left click anywhere also advances
        if (Input.GetMouseButtonDown(0))
        {
            AdvancePage();
        }
    }

    public void AdvancePage()
    {
        if (pages == null || pages.Length == 0)
            return;

        currentPage = Mathf.Clamp(currentPage + 1, 0, pages.Length);
        if (currentPage >= pages.Length)
        {
            // clamp to last page
            currentPage = pages.Length - 1;
            // optionally: signal end
        }
        Refresh();
    }

    void Refresh()
    {
        if (displayText != null && pages != null && pages.Length > 0)
        {
            displayText.text = pages[currentPage];
        }
    }
}
