/********************************************************************************
** Form generated from reading UI file 'DoneSpecWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DONESPECWIDGET_H
#define UI_DONESPECWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_DoneSpecWidget
{
public:
    QHBoxLayout *horizontalLayout;
    QToolButton *remove;
    QFrame *line;
    QLabel *varName;
    QCheckBox *delta;
    QLabel *label;
    QComboBox *operation;
    QSpinBox *reference;

    void setupUi(QWidget *DoneSpecWidget)
    {
        if (DoneSpecWidget->objectName().isEmpty())
            DoneSpecWidget->setObjectName(QString::fromUtf8("DoneSpecWidget"));
        DoneSpecWidget->resize(413, 31);
        horizontalLayout = new QHBoxLayout(DoneSpecWidget);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        horizontalLayout->setContentsMargins(0, 0, 0, 0);
        remove = new QToolButton(DoneSpecWidget);
        remove->setObjectName(QString::fromUtf8("remove"));

        horizontalLayout->addWidget(remove);

        line = new QFrame(DoneSpecWidget);
        line->setObjectName(QString::fromUtf8("line"));
        QSizePolicy sizePolicy(QSizePolicy::Fixed, QSizePolicy::Ignored);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(line->sizePolicy().hasHeightForWidth());
        line->setSizePolicy(sizePolicy);
        line->setFrameShape(QFrame::VLine);
        line->setFrameShadow(QFrame::Sunken);

        horizontalLayout->addWidget(line);

        varName = new QLabel(DoneSpecWidget);
        varName->setObjectName(QString::fromUtf8("varName"));
        QFont font;
        font.setItalic(true);
        varName->setFont(font);

        horizontalLayout->addWidget(varName);

        delta = new QCheckBox(DoneSpecWidget);
        delta->setObjectName(QString::fromUtf8("delta"));

        horizontalLayout->addWidget(delta);

        label = new QLabel(DoneSpecWidget);
        label->setObjectName(QString::fromUtf8("label"));

        horizontalLayout->addWidget(label);

        operation = new QComboBox(DoneSpecWidget);
        operation->setObjectName(QString::fromUtf8("operation"));

        horizontalLayout->addWidget(operation);

        reference = new QSpinBox(DoneSpecWidget);
        reference->setObjectName(QString::fromUtf8("reference"));
        reference->setAccelerated(true);
        reference->setMinimum(-2147483647);
        reference->setMaximum(2147483647);
        reference->setValue(0);

        horizontalLayout->addWidget(reference);


        retranslateUi(DoneSpecWidget);

        QMetaObject::connectSlotsByName(DoneSpecWidget);
    } // setupUi

    void retranslateUi(QWidget *DoneSpecWidget)
    {
        DoneSpecWidget->setWindowTitle(QCoreApplication::translate("DoneSpecWidget", "Form", nullptr));
        remove->setText(QCoreApplication::translate("DoneSpecWidget", "-", nullptr));
        varName->setText(QCoreApplication::translate("DoneSpecWidget", "{varName}", nullptr));
        delta->setText(QCoreApplication::translate("DoneSpecWidget", "delta", nullptr));
        label->setText(QCoreApplication::translate("DoneSpecWidget", "is", nullptr));
    } // retranslateUi

};

namespace Ui {
    class DoneSpecWidget: public Ui_DoneSpecWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DONESPECWIDGET_H
