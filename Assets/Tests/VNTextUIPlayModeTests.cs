using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UI;

public class VNTextUIPlayModeTests
{
    GameObject go;
    VNInputHandler handler;

    [UnitySetUp]
    public IEnumerator SetUp()
    {
        go = new GameObject("VNTestRoot");
        var canvasGO = new GameObject("Canvas");
        var canvas = canvasGO.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvasGO.transform.SetParent(go.transform);

        var textGO = new GameObject("Text");
        textGO.transform.SetParent(canvasGO.transform);
        var text = textGO.AddComponent<Text>();
        text.font = Resources.GetBuiltinResource<Font>("Arial.ttf");

        var buttonGO = new GameObject("NextButton");
        buttonGO.transform.SetParent(canvasGO.transform);
        var button = buttonGO.AddComponent<Button>();

        handler = go.AddComponent<VNInputHandler>();
        handler.displayText = text;
        handler.nextButton = button;
        handler.pages = new string[] { "One", "Two", "Three" };

        yield return null; // wait a frame for Awake/Start
    }

    [UnityTest]
    public IEnumerator ClickAdvancesPage()
    {
        Assert.AreEqual(0, handler.currentPage);
        // simulate button click
        handler.nextButton.onClick.Invoke();
        yield return null;
        Assert.AreEqual(1, handler.currentPage);
        Assert.AreEqual("Two", handler.displayText.text);
    }

    [UnityTest]
    public IEnumerator SpaceKeyAdvancesPage()
    {
        handler.currentPage = 0;
        yield return null;
        // simulate space key by calling AdvancePage (Input simulation in tests is limited)
        handler.AdvancePage();
        yield return null;
        Assert.AreEqual(1, handler.currentPage);
    }

    [UnityTearDown]
    public IEnumerator TearDown()
    {
        Object.DestroyImmediate(go);
        yield return null;
    }
}
